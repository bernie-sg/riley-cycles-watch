#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <fstream>
#include <algorithm>
#include <iomanip>
#include <sstream>

using namespace std;
using Complex = complex<double>;

// High-Q Morlet wavelet
vector<Complex> create_high_q_morlet(double freq, int len) {
    vector<Complex> wavelet(len);
    double Q = 15.0 + 50.0 * freq;
    double sigma = Q / (2.0 * M_PI * freq);

    for (int i = 0; i < len; i++) {
        double t = i - len/2.0;
        double envelope = exp(-t * t / (2.0 * sigma * sigma));
        Complex carrier = exp(Complex(0, 2.0 * M_PI * freq * t));
        wavelet[i] = envelope * carrier;
    }

    double norm = 0;
    for (const auto& w : wavelet) {
        norm += abs(w) * abs(w);
    }
    norm = sqrt(norm);
    for (auto& w : wavelet) w /= norm;

    return wavelet;
}

double compute_power(const vector<double>& data, int wavelength) {
    int n = data.size();
    if (wavelength > n/2) return 0;

    double freq = 1.0 / wavelength;
    int cycles = min(8, max(4, n / wavelength));
    int wlen = min(n, wavelength * cycles);

    vector<Complex> wavelet = create_high_q_morlet(freq, wlen);

    double total_power = 0;
    int count = 0;
    int step = max(1, wavelength / 8);

    for (int center = wlen/2; center <= n - wlen/2; center += step) {
        Complex sum = 0;
        for (int i = 0; i < wlen; i++) {
            int idx = center - wlen/2 + i;
            if (idx >= 0 && idx < n) {
                sum += data[idx] * conj(wavelet[i]);
            }
        }
        total_power += abs(sum) * abs(sum);
        count++;
    }

    return count > 0 ? sqrt(total_power / count) : 0;
}

vector<double> process_spectrum(vector<double>& spectrum) {
    // Median filter
    int window = 3;
    vector<double> filtered = spectrum;
    for (size_t i = window; i < spectrum.size() - window; i++) {
        vector<double> vals;
        for (int j = -window; j <= window; j++) {
            vals.push_back(spectrum[i + j]);
        }
        sort(vals.begin(), vals.end());
        filtered[i] = vals[vals.size() / 2];
    }

    // Smooth
    window = 10;
    vector<double> smoothed(filtered.size());
    for (size_t i = 0; i < filtered.size(); i++) {
        double sum = 0;
        double weight = 0;
        for (int j = -window; j <= window; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < (int)filtered.size()) {
                double sigma = window / 3.0;
                double w = exp(-0.5 * (j * j) / (sigma * sigma));
                sum += filtered[idx] * w;
                weight += w;
            }
        }
        smoothed[i] = sum / weight;
    }

    // Enhance peaks
    double mean = 0;
    for (double s : smoothed) mean += s;
    mean /= smoothed.size();

    vector<double> enhanced(smoothed.size());
    for (size_t i = 0; i < smoothed.size(); i++) {
        if (smoothed[i] > mean) {
            enhanced[i] = mean + (smoothed[i] - mean) * 2.0;
        } else {
            enhanced[i] = smoothed[i];
        }
    }

    // Final smooth
    window = 5;
    vector<double> final(enhanced.size());
    for (size_t i = 0; i < enhanced.size(); i++) {
        double sum = 0;
        double weight = 0;
        for (int j = -window; j <= window; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < (int)enhanced.size()) {
                double sigma = window / 3.0;
                double w = exp(-0.5 * (j * j) / (sigma * sigma));
                sum += enhanced[idx] * w;
                weight += w;
            }
        }
        final[i] = sum / weight;
    }

    // Normalize
    double max_val = *max_element(final.begin(), final.end());
    if (max_val > 0) {
        for (auto& s : final) s /= max_val;
    }

    return final;
}

int main() {
    cout << "==============================================\n";
    cout << "GENERATING WEEKLY SCANNERS (200 weeks)\n";
    cout << "==============================================\n\n";

    // Load all data
    vector<double> prices;
    ifstream file("tlt_prices.txt");
    if (!file) {
        cerr << "Cannot open tlt_prices.txt\n";
        return 1;
    }
    double price;
    while (file >> price) prices.push_back(price);
    file.close();

    cout << "Total data points: " << prices.size() << "\n";
    cout << "Generating weekly scanners from week 0 to week 200\n";
    cout << "Using 4000 bars constant window\n";
    cout << "Scanning 100-800 wavelength\n\n";

    // Store all peak data for heatmap
    vector<vector<pair<int, double>>> all_peaks;

    // Generate scanners for each week (5 years = 260 weeks)
    for (int week = 0; week <= 260; week++) {
        int rollback = week * 5;  // 5 trading days per week
        int window_size = 4000;
        int end_idx = prices.size() - rollback;
        int start_idx = end_idx - window_size;

        if (start_idx < 0) {
            cout << "Week " << week << ": Not enough data\n";
            continue;
        }

        // Process data
        vector<double> data(window_size);
        double sum_x = 0, sum_y = 0, sum_xx = 0, sum_xy = 0;
        for (int i = 0; i < window_size; i++) {
            double y = log(prices[start_idx + i]);
            sum_x += i;
            sum_y += y;
            sum_xx += i * i;
            sum_xy += i * y;
        }

        double slope = (window_size * sum_xy - sum_x * sum_y) / (window_size * sum_xx - sum_x * sum_x);
        double intercept = (sum_y - slope * sum_x) / window_size;

        for (int i = 0; i < window_size; i++) {
            data[i] = log(prices[start_idx + i]) - (intercept + slope * i);
        }

        // Compute spectrum
        vector<double> spectrum;
        vector<int> wavelengths;

        for (int wl = 100; wl <= 800; wl++) {
            double power = compute_power(data, wl);
            spectrum.push_back(power);
            wavelengths.push_back(wl);
        }

        // Process spectrum
        spectrum = process_spectrum(spectrum);

        // Find peaks
        vector<pair<int, double>> peaks;
        for (size_t i = 10; i < spectrum.size() - 10; i++) {
            bool is_peak = true;
            for (int j = -10; j <= 10; j++) {
                if (j != 0 && spectrum[i + j] > spectrum[i]) {
                    is_peak = false;
                    break;
                }
            }
            if (is_peak && spectrum[i] > 0.05) {
                peaks.push_back({wavelengths[i], spectrum[i]});
            }
        }

        all_peaks.push_back(peaks);

        // Sort peaks by power
        sort(peaks.begin(), peaks.end(),
             [](const auto& a, const auto& b) { return a.second > b.second; });

        // Output data for EVERY week (not just every 10th)
        cout << "Week " << setw(3) << week << ": ";
        for (const auto& peak : peaks) {
            int cal_days = peak.first * 1.451;
            if (peak.second > 0.2) {  // Only show significant peaks
                cout << cal_days << "d(" << fixed << setprecision(1) << (peak.second*100) << "%) ";
            }
        }
        cout << "\n";
    }

    // Generate heatmap HTML
    cout << "\nGenerating weekly heatmap...\n";

    ofstream html("weekly_heatmap.html");
    html << R"(<!DOCTYPE html>
<html>
<head>
<title>Weekly Resolution Heatmap - 5 Years</title>
<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
<style>
body {
    background: #000;
    color: #fff;
    font-family: monospace;
    margin: 0;
    padding: 10px;
}
h1 {
    text-align: center;
    color: #0ff;
}
</style>
</head>
<body>
<h1>WEEKLY RESOLUTION - 5 YEARS - Peak Evolution Heatmap</h1>
<div id='heatmap' style='width:100%;height:85vh;'></div>
<script>
// Create heatmap data
const weeks = 261;  // 0 to 260 weeks (5 years)
const minWave = 100;  // Start at 100 trading days
const maxWave = 800;  // End at 800 trading days
const waveStep = 1;   // 1 day resolution
const wavePoints = maxWave - minWave + 1;

let z = Array(wavePoints).fill().map(() => Array(weeks).fill(0));

// Peak data
const peakData = [)";

    // Output peak data (using trading days directly)
    for (size_t week = 0; week < all_peaks.size(); week++) {
        for (const auto& peak : all_peaks[week]) {
            int trading_days = peak.first;  // Use trading days directly
            html << "\n    [" << week << ", " << trading_days << ", " << peak.second << "],";
        }
    }

    html << R"(
];

// Fill heatmap - REVERSE time axis so NOW is on right
peakData.forEach(([week, wavelength, power]) => {
    const waveIdx = wavelength - minWave;  // Direct index since we're using trading days
    const timeIdx = weeks - 1 - week;  // REVERSE: week 0 goes to position 260
    if (waveIdx >= 0 && waveIdx < wavePoints && timeIdx >= 0 && timeIdx < weeks) {
        // Set peak with gaussian spread proportional to power
        const spread = Math.max(2, Math.floor(power * 5));
        for (let i = Math.max(0, waveIdx - spread); i <= Math.min(wavePoints - 1, waveIdx + spread); i++) {
            const distance = Math.abs(i - waveIdx);
            const intensity = power * Math.exp(-distance * distance / (spread * spread));
            z[i][timeIdx] = Math.max(z[i][timeIdx], intensity);
        }
    }
});

// X-axis labels - REVERSED so NOW is on right
const xLabels = Array(weeks).fill().map((_, i) => {
    const weeksAgo = weeks - 1 - i;  // Reverse the count
    if (weeksAgo === 0) return 'NOW';
    if (weeksAgo % 52 === 0) return `-${weeksAgo/52}yr`;
    if (weeksAgo % 13 === 0 && weeksAgo < 52) return `-${weeksAgo}w`;
    return '';
});

// Y-axis labels (wavelengths in calendar days)
const yLabels = Array(wavePoints).fill().map((_, i) => {
    const tradingDays = minWave + i;
    const calendarDays = Math.round(tradingDays * 1.451);
    if (tradingDays % 100 === 0) return calendarDays;
    return '';
});

const data = [{
    z: z,
    x: xLabels,
    y: yLabels,
    type: 'heatmap',
    colorscale: [
        [0, '#000000'],
        [0.1, '#001133'],
        [0.3, '#003388'],
        [0.5, '#0066ff'],
        [0.7, '#00aaff'],
        [1.0, '#ffffff']
    ],
    showscale: false
}];

const layout = {
    title: {
        text: 'WEEKLY RESOLUTION - 5 YEARS (260 weeks) - 4000 bars sliding window - 100-800 wavelength scan',
        font: { color: '#0ff', size: 14 }
    },
    xaxis: {
        title: 'Time (Weeks Ago)',
        titlefont: { color: '#fff' },
        tickfont: { color: '#888' },
        gridcolor: '#222',
        range: [0, 260]
    },
    yaxis: {
        title: 'Wavelength (Calendar Days)',
        titlefont: { color: '#fff' },
        tickfont: { color: '#888' },
        gridcolor: '#222',
        range: [145, 1160]  // 100 to 800 trading days in calendar days
    },
    plot_bgcolor: '#000',
    paper_bgcolor: '#000'
};

Plotly.newPlot('heatmap', data, layout, {responsive: true});
</script>
</body>
</html>)";

    html.close();

    cout << "\nComplete! Files generated:\n";
    cout << "- weekly_heatmap.html\n";
    cout << "\nShowing persistent cycles as horizontal bands\n";
    cout << "Weekly resolution from week 0 (current) to week 260\n";
    cout << "Total weeks processed: " << all_peaks.size() << "\n";

    return 0;
}