#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <fstream>
#include <algorithm>
#include <iomanip>

using namespace std;
using Complex = complex<double>;

// EXACT SAME CODE FROM scanner_clean.cpp that was working
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

    if (count > 0) {
        return sqrt(total_power / count);
    }
    return 0;
}

// EXACT smoothing from scanner_clean
vector<double> smooth_spectrum(const vector<double>& spectrum, int window = 5) {
    int n = spectrum.size();
    vector<double> smoothed(n);

    for (int i = 0; i < n; i++) {
        double sum = 0;
        double weight = 0;
        for (int j = -window; j <= window; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < n) {
                double sigma = window / 3.0;
                double w = exp(-0.5 * (j * j) / (sigma * sigma));
                sum += spectrum[idx] * w;
                weight += w;
            }
        }
        smoothed[i] = sum / weight;
    }
    return smoothed;
}

vector<double> median_filter(const vector<double>& spectrum, int window = 3) {
    int n = spectrum.size();
    vector<double> filtered(n);

    for (int i = 0; i < n; i++) {
        vector<double> values;
        for (int j = -window; j <= window; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < n) {
                values.push_back(spectrum[idx]);
            }
        }
        sort(values.begin(), values.end());
        filtered[i] = values[values.size()/2];
    }
    return filtered;
}

vector<double> enhance_peaks(const vector<double>& spectrum, double factor = 2.0) {
    int n = spectrum.size();
    vector<double> enhanced(n);

    double mean = 0;
    for (double s : spectrum) mean += s;
    mean /= n;

    for (int i = 0; i < n; i++) {
        if (spectrum[i] > mean) {
            double excess = spectrum[i] - mean;
            enhanced[i] = mean + excess * factor;
        } else {
            enhanced[i] = spectrum[i];
        }
    }
    return enhanced;
}

int main() {
    cout << "SIMPLE HEATMAP - Using working scanner logic\n";
    cout << "============================================\n\n";

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

    const int total_weeks = 260;
    const int window_size = 4000;

    // Store all spectra
    vector<vector<double>> all_spectra;

    // Process each week using EXACT scanner_clean logic
    for (int week = 0; week <= total_weeks; week++) {
        int rollback = week * 5;
        int end_idx = prices.size() - rollback;
        int start_idx = end_idx - window_size;

        if (start_idx < 0) {
            all_spectra.push_back(vector<double>(701, 0));
            continue;
        }

        // Use recent data - SAME AS scanner_clean
        vector<double> data(window_size);

        // Log transform and detrend - SAME AS scanner_clean
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

        // Scan with fine resolution - SAME AS scanner_clean
        vector<double> spectrum;
        for (int wl = 100; wl <= 800; wl++) {
            double power = compute_power(data, wl);
            spectrum.push_back(power);
        }

        // Apply EXACT same processing as scanner_clean
        spectrum = median_filter(spectrum, 3);
        spectrum = smooth_spectrum(spectrum, 10);
        spectrum = enhance_peaks(spectrum, 2.0);
        spectrum = smooth_spectrum(spectrum, 5);

        // Adaptive smoothing - SAME AS scanner_clean
        double threshold = 0.3;
        for (int pass = 0; pass < 2; pass++) {
            vector<double> adaptive_smooth = spectrum;
            for (size_t i = 5; i < spectrum.size() - 5; i++) {
                if (spectrum[i] < threshold) {
                    double sum = 0;
                    double weight = 0;
                    for (int j = -5; j <= 5; j++) {
                        double w = exp(-0.5 * j * j / 4.0);
                        sum += spectrum[i + j] * w;
                        weight += w;
                    }
                    adaptive_smooth[i] = sum / weight;
                }
            }
            spectrum = adaptive_smooth;
        }

        // Normalize
        double max_val = *max_element(spectrum.begin(), spectrum.end());
        if (max_val > 0) {
            for (auto& s : spectrum) s /= max_val;
        }

        // Debug: Show peaks for week 0
        if (week == 0) {
            cout << "Week 0 spectrum peaks:\n";
            for (size_t i = 10; i < spectrum.size() - 10; i++) {
                bool is_peak = true;
                for (int j = -10; j <= 10; j++) {
                    if (j != 0 && spectrum[i + j] > spectrum[i]) {
                        is_peak = false;
                        break;
                    }
                }
                if (is_peak && spectrum[i] > 0.2) {
                    int wl = 100 + i;
                    int cal_days = wl * 1.451;
                    cout << "  Peak at " << cal_days << "d (power=" << spectrum[i] << ")\n";
                }
            }
        }

        all_spectra.push_back(spectrum);

        if (week % 20 == 0) {
            cout << "Processed week " << week << "\n";
        }
    }

    // Generate HTML
    ofstream html("simple_heatmap_fixed.html");
    html << R"(<!DOCTYPE html>
<html>
<head>
<title>Weekly Heatmap - Working Scanner Logic</title>
<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
<style>
body { background: #000; color: #fff; font-family: monospace; margin: 0; padding: 10px; }
h1 { text-align: center; color: #0ff; font-size: 20px; }
</style>
</head>
<body>
<h1>WEEKLY HEATMAP - 260 WEEKS - Using Working Scanner Logic</h1>
<div id='heatmap' style='width:100%;height:85vh;'></div>
<script>
var z_data = [
)";

    // Output data - wavelength rows, time columns (REVERSED)
    for (int wl = 0; wl < 701; wl++) {
        html << "  [";
        for (int week = total_weeks; week >= 0; week--) {  // REVERSED: NOW on right
            if (!all_spectra[week].empty() && wl < (int)all_spectra[week].size()) {
                html << fixed << setprecision(3) << all_spectra[week][wl];
            } else {
                html << "0";
            }
            if (week > 0) html << ",";
        }
        html << "]";
        if (wl < 700) html << ",";
        html << "\n";
    }

    html << R"(];

// Debug: Check data values
console.log('Data shape:', z_data.length, 'x', z_data[0].length);
let maxVal = 0;
let nonZeroCount = 0;
for (let i = 0; i < z_data.length; i++) {
    for (let j = 0; j < z_data[i].length; j++) {
        if (z_data[i][j] > maxVal) maxVal = z_data[i][j];
        if (z_data[i][j] > 0.01) nonZeroCount++;
    }
}
console.log('Max value:', maxVal);
console.log('Non-zero values:', nonZeroCount);

// X-axis labels (NOW on right)
var x_labels = [];
for (let i = 0; i <= 260; i++) {
    let week = 260 - i;
    if (week === 0) x_labels.push('NOW');
    else if (week === 52) x_labels.push('1yr');
    else if (week === 104) x_labels.push('2yr');
    else if (week === 156) x_labels.push('3yr');
    else if (week === 208) x_labels.push('4yr');
    else if (week === 260) x_labels.push('5yr');
    else x_labels.push('');
}

// Y-axis in calendar days
var y_labels = [];
for (let i = 0; i <= 700; i++) {
    let trading = 100 + i;
    let calendar = Math.round(trading * 1.451);
    if (trading % 100 === 0) y_labels.push(calendar);
    else y_labels.push('');
}

var data = [{
    z: z_data,
    x: x_labels,
    y: y_labels,
    type: 'heatmap',
    colorscale: [
        [0.0, '#000000'],
        [0.1, '#001122'],
        [0.2, '#003366'],
        [0.3, '#0066aa'],
        [0.5, '#0099ff'],
        [0.7, '#66ccff'],
        [1.0, '#ffffff']
    ],
    zmin: 0,
    zmax: 1,
    showscale: true
}];

var layout = {
    title: {
        text: '5 YEARS WEEKLY - Same scanner_clean logic - 100-800 wavelength',
        font: { color: '#0ff', size: 14 }
    },
    xaxis: {
        title: 'Time (NOW on right →)',
        titlefont: { color: '#fff' },
        tickfont: { color: '#888' },
        gridcolor: '#222'
    },
    yaxis: {
        title: 'Wavelength (Calendar Days)',
        titlefont: { color: '#fff' },
        tickfont: { color: '#888' },
        gridcolor: '#222',
        tickmode: 'array',
        tickvals: [0, 100, 200, 300, 400, 500, 600, 700],
        ticktext: ['145', '290', '435', '580', '725', '870', '1015', '1160']
    },
    plot_bgcolor: '#000',
    paper_bgcolor: '#000'
};

Plotly.newPlot('heatmap', data, layout, {responsive: true});
</script>
</body>
</html>)";

    html.close();

    cout << "\n============================================\n";
    cout << "Generated: simple_heatmap_fixed.html\n";
    cout << "Using EXACT scanner_clean logic that was working\n";

    return 0;
}