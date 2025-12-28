#!/bin/bash
# Bandpass Algorithm Build and Run Scripts

echo "========================================="
echo "BANDPASS ALGORITHM BUILD & RUN"
echo "========================================="
echo ""

# Navigate to project directory
cd "/Users/bernie/Documents/Cycles Detector"

echo "Select option:"
echo "1. Run Uniform Sine Wave Bandpass (Python)"
echo "2. Run MA Difference Bandpass (Python)"
echo "3. Generate 260-day cycle visualization"
echo "4. Generate 531-day cycle visualization"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "Running uniform sine wave bandpass..."
        python3 algorithms/bandpass/sigma_l_bandpass_filter.py --wavelength 260
        ;;
    2)
        echo "Running MA difference bandpass..."
        python3 algorithms/bandpass/bandpass_algo.py --symbol TLT --wavelength 531
        ;;
    3)
        echo "Generating 260-day cycle visualization..."
        python3 algorithms/bandpass/sigma_l_bandpass_filter.py --wavelength 260 --length 2500
        open bandpass_filter.png
        ;;
    4)
        echo "Generating 531-day cycle visualization..."
        python3 algorithms/bandpass/sigma_l_bandpass_filter.py --wavelength 531 --length 4000
        open bandpass_filter.png
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"