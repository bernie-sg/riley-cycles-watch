#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <fstream>
#include <algorithm>
#include <iomanip>

using namespace std;
using Complex = complex<double>;

// High-Q Morlet wavelet for frequency selectivity
vector<Complex> create_high_q_morlet(double freq, int len) {
    vector<Complex> wavelet(len);

    // Very high Q for sharp frequency resolution
    // Q = center_frequency / bandwidth
    double Q = 15.0 + 50.0 * freq;  // Higher Q for lower frequencies
    double sigma = Q / (2.0 * M_PI * freq);

    for (int i = 0; i < len; i++) {
        double t = i - len/2.0;

        // Gaussian envelope
        double envelope = exp(-t * t / (2.0 * sigma * sigma));

        // Complex carrier wave
        Complex carrier = exp(Complex(0, 2.0 * M_PI * freq * t));

        wavelet[i] = envelope * carrier;
    }

    // Normalize
    double norm = 0;
    for (const auto& w : wavelet) {
        norm += abs(w) * abs(w);
    }
    norm = sqrt(norm);

    for (auto& w : wavelet) {
        w /= norm;
    }

    return wavelet;
}

// Compute power at specific wavelength
double compute_power(const vector<double>& data, int wavelength) {
    int n = data.size();
    if (wavelength > n/2) return 0;

    double freq = 1.0 / wavelength;

    // Use sufficient cycles for good resolution
    int cycles = min(8, max(4, n / wavelength));
    int wlen = min(n, wavelength * cycles);

    vector<Complex> wavelet = create_high_q_morlet(freq, wlen);

    // Scan across data
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

        total_power += abs(sum) * abs(sum);  // Power = |amplitude|^2
        count++;
    }

    if (count > 0) {
        return sqrt(total_power / count);  // RMS power
    }

    return 0;
}

// Smooth spectrum to remove artifacts
vector<double> smooth_spectrum(const vector<double>& spectrum, int window = 5) {
    int n = spectrum.size();
    vector<double> smoothed(n);

    for (int i = 0; i < n; i++) {
        double sum = 0;
        double weight = 0;

        for (int j = -window; j <= window; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < n) {
                // Gaussian weights with proper sigma
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

// Median filter to remove spike noise
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

// Enhance peaks while preserving smooth shape
vector<double> enhance_peaks(const vector<double>& spectrum, double factor = 2.0) {
    int n = spectrum.size();
    vector<double> enhanced(n);

    // Find mean for thresholding
    double mean = 0;
    for (double s : spectrum) mean += s;
    mean /= n;

    for (int i = 0; i < n; i++) {
        // Non-linear enhancement: amplify values above mean
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
    cout << "==============================================\n";
    cout << "CLEAN HIGH-Q SCANNER - No Artifacts\n";
    cout << "==============================================\n\n";

    // Load data
    vector<double> prices;
    ifstream file("tlt_prices.txt");
    if (!file) {
        cerr << "Cannot open tlt_prices.txt\n";
        return 1;
    }
    double price;
    while (file >> price) prices.push_back(price);
    file.close();

    // Use recent data
    int window = min(2000, (int)prices.size());
    vector<double> data(window);

    // Log transform and detrend
    double sum_x = 0, sum_y = 0, sum_xx = 0, sum_xy = 0;
    for (int i = 0; i < window; i++) {
        double y = log(prices[prices.size() - window + i]);
        sum_x += i;
        sum_y += y;
        sum_xx += i * i;
        sum_xy += i * y;
    }

    double slope = (window * sum_xy - sum_x * sum_y) / (window * sum_xx - sum_x * sum_x);
    double intercept = (sum_y - slope * sum_x) / window;

    for (int i = 0; i < window; i++) {
        data[i] = log(prices[prices.size() - window + i]) - (intercept + slope * i);
    }

    cout << "Analyzing " << window << " days of TLT data\n";
    cout << "High-Q scanning from 30 to 1000 days\n\n";

    // Scan with fine resolution
    vector<double> spectrum;
    vector<int> wavelengths;

    cout << "Computing high-Q spectrum: ";
    for (int wl = 30; wl <= 1000; wl++) {
        double power = compute_power(data, wl);
        spectrum.push_back(power);
        wavelengths.push_back(wl);

        if (wl % 100 == 0) {
            cout << wl << ".. ";
            cout.flush();
        }
    }
    cout << "Done!\n";

    // Remove spike noise first with median filter
    cout << "Removing noise...\n";
    spectrum = median_filter(spectrum, 3);  // Slightly wider median filter

    // Then smooth to get nice curves
    cout << "Smoothing spectrum...\n";
    spectrum = smooth_spectrum(spectrum, 10);  // Even wider window for smoother curves

    // Enhance peaks more strongly
    cout << "Enhancing peaks...\n";
    spectrum = enhance_peaks(spectrum, 2.0);

    // Final smoothing pass to ensure no artifacts
    spectrum = smooth_spectrum(spectrum, 5);

    // Apply adaptive smoothing - more smoothing in valleys, less on peaks
    cout << "Adaptive smoothing...\n";
    double threshold = 0.3;  // Values below this get extra smoothing
    for (int pass = 0; pass < 2; pass++) {
        vector<double> adaptive_smooth = spectrum;
        for (size_t i = 5; i < spectrum.size() - 5; i++) {
            if (spectrum[i] < threshold) {
                // Apply local smoothing to low regions
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
    for (auto& s : spectrum) s /= max_val;

    // Find peaks
    vector<pair<int, double>> peaks;
    for (size_t i = 10; i < spectrum.size() - 10; i++) {
        bool is_peak = true;

        // Check if local maximum
        for (int j = -10; j <= 10; j++) {
            if (j != 0 && spectrum[i + j] > spectrum[i]) {
                is_peak = false;
                break;
            }
        }

        // Include all peaks, even smaller ones for tracking
        if (is_peak && spectrum[i] > 0.05) {  // Lower threshold to catch secondary/tertiary peaks
            peaks.push_back({wavelengths[i], spectrum[i]});
        }
    }

    // Sort by power
    sort(peaks.begin(), peaks.end(),
         [](const auto& a, const auto& b) { return a.second > b.second; });

    cout << "\n==============================================\n";
    cout << "ALL DETECTED PEAKS (30-1000 days):\n";
    cout << "==============================================\n\n";

    for (size_t i = 0; i < peaks.size(); i++) {
        int wl_t = peaks[i].first;
        int wl_c = wl_t * 1.451;
        double power = peaks[i].second * 100;

        cout << setw(2) << (i+1) << ". ";
        cout << setw(4) << wl_t << " trading = ";
        cout << setw(4) << wl_c << " calendar days";
        cout << "  [" << fixed << setprecision(1) << power << "%]";

        // Label peak significance
        if (power > 25) {
            cout << " *** PRIMARY";
        } else if (power > 15) {
            cout << " ** SECONDARY";
        } else if (power > 8) {
            cout << " * TERTIARY";
        }
        cout << "\n";
    }

    // Save results
    ofstream out("clean_spectrum.txt");
    out << "# Wavelength_Trading Wavelength_Calendar Power\n";
    for (size_t i = 0; i < spectrum.size(); i++) {
        out << wavelengths[i] << " " << (wavelengths[i] * 1.451) << " " << spectrum[i] << "\n";
    }
    out.close();

    // Generate HTML
    ofstream html("scanner_clean.html");
    html << R"(<!DOCTYPE html>
<html>
<head>
<title>Clean High-Q Scanner</title>
<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
<style>
body {
    background: #000;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    margin: 0;
    padding: 0;
}
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}
h1 {
    text-align: center;
    color: #00ffff;
    font-weight: 300;
    letter-spacing: 2px;
    margin-bottom: 30px;
}
#chart {
    width: 100%;
    height: 70vh;
    min-height: 500px;
    background: #0a0a0a;
    border-radius: 8px;
    box-shadow: 0 0 40px rgba(0,255,255,0.1);
}
.info {
    margin-top: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #0a0a0a, #1a1a1a);
    border-radius: 8px;
    border-left: 3px solid #00ffff;
}
</style>
</head>
<body>
<div class="container">
<h1>CLEAN HIGH-Q WAVELET SCANNER</h1>
<div id='chart'></div>
<div class='info'>
<h3 style="color:#00ffff;">Sharp Peak Detection</h3>
<p>High Q-factor Morlet wavelets with adaptive bandwidth for sharp frequency resolution.</p>
<p>Smoothed spectrum with gentle peak enhancement - no artifacts.</p>
</div>
</div>
<script>
var data = [)";

    // Output spectrum data
    for (size_t i = 0; i < spectrum.size(); i++) {
        if (i > 0) html << ",";
        html << "[" << (wavelengths[i] * 1.451) << "," << spectrum[i] << "]";
    }
    html << "];\n";

    // Output ALL peak data with labels
    html << "var peaks = [";
    for (size_t i = 0; i < peaks.size(); i++) {
        if (i > 0) html << ",";
        html << "[" << (peaks[i].first * 1.451) << "," << peaks[i].second << "]";
    }
    html << "];\n";

    // Create labels for peaks
    html << "var peakLabels = [";
    for (size_t i = 0; i < peaks.size(); i++) {
        if (i > 0) html << ",";
        int cal_days = peaks[i].first * 1.451;
        double power = peaks[i].second * 100;
        html << "\"" << cal_days << "d";
        if (power > 25) {
            html << " (PRIMARY)";
        } else if (power > 15) {
            html << " (SECONDARY)";
        } else if (power > 8) {
            html << " (TERTIARY)";
        }
        html << "\"";
    }
    html << "];\n";

    html << R"(
var x = data.map(d => d[0]);
var y = data.map(d => d[1]);

var trace1 = {
    x: x,
    y: y,
    type: 'scatter',
    mode: 'lines',
    name: 'Spectrum',
    line: {
        color: '#00ffff',
        width: 2,
        shape: 'spline',
        smoothing: 0.8
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(0,255,255,0.05)'
};

var trace2 = {
    x: peaks.map(p => p[0]),
    y: peaks.map(p => p[1]),
    type: 'scatter',
    mode: 'markers+text',
    name: 'Peaks',
    marker: {
        color: peaks.map(p => p[1] > 0.25 ? '#ff0000' : p[1] > 0.15 ? '#ffff00' : '#00ff00'),
        size: peaks.map(p => p[1] > 0.25 ? 15 : p[1] > 0.15 ? 12 : 10),
        symbol: 'diamond',
        line: {
            color: '#fff',
            width: 1
        }
    },
    text: peakLabels,
    textposition: 'top',
    textfont: {
        color: peaks.map(p => p[1] > 0.25 ? '#ff0000' : p[1] > 0.15 ? '#ffff00' : '#00ff00'),
        size: peaks.map(p => p[1] > 0.25 ? 12 : 10)
    }
};

var layout = {
    title: {
        text: 'High-Q Wavelet Transform Spectrum',
        font: { color: '#00ffff', size: 14 }
    },
    xaxis: {
        title: 'Wavelength (calendar days)',
        color: '#666',
        gridcolor: '#222',
        zerolinecolor: '#333',
        tickfont: { size: 11 }
    },
    yaxis: {
        title: 'Normalized Power',
        color: '#666',
        gridcolor: '#222',
        zerolinecolor: '#333',
        tickfont: { size: 11 }
    },
    plot_bgcolor: '#0a0a0a',
    paper_bgcolor: '#000',
    showlegend: true,
    legend: {
        font: { color: '#ccc' },
        bgcolor: 'rgba(0,0,0,0.7)',
        bordercolor: '#333',
        borderwidth: 1
    },
    hovermode: 'closest'
};

var config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false
};

Plotly.newPlot('chart', [trace1, trace2], layout, config);
</script>
</body>
</html>)";
    html.close();

    cout << "\nOutput saved to scanner_clean.html\n";
    cout << "==============================================\n";

    return 0;
}