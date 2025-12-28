#!/bin/bash
# Scanner_Clean Build and Run Scripts

echo "========================================="
echo "SCANNER_CLEAN BUILD & RUN"
echo "========================================="
echo ""

# Navigate to project directory
cd "/Users/bernie/Documents/Cycles Detector"

echo "Select option:"
echo "1. Build & Run Basic Scanner"
echo "2. Build & Run Weekly Heatmap (BEST)"
echo "3. Build & Run Simple Heatmap"
echo "4. Build All"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "Building scanner_clean..."
        g++ -O3 -o scanner_clean algorithms/scanner_clean/scanner_clean.cpp
        echo "Running scanner..."
        ./scanner_clean
        ;;
    2)
        echo "Building generate_weekly_scanners..."
        g++ -O3 -o generate_weekly_scanners algorithms/scanner_clean/generate_weekly_scanners.cpp
        echo "Generating weekly heatmap..."
        ./generate_weekly_scanners
        echo "Opening heatmap..."
        open weekly_heatmap.html
        ;;
    3)
        echo "Building simple_heatmap_fixed..."
        g++ -O3 -o simple_heatmap_fixed algorithms/scanner_clean/simple_heatmap_fixed.cpp
        echo "Running simple heatmap..."
        ./simple_heatmap_fixed
        open simple_heatmap_fixed.html
        ;;
    4)
        echo "Building all implementations..."
        g++ -O3 -o scanner_clean algorithms/scanner_clean/scanner_clean.cpp
        echo "✓ scanner_clean built"
        g++ -O3 -o generate_weekly_scanners algorithms/scanner_clean/generate_weekly_scanners.cpp
        echo "✓ generate_weekly_scanners built"
        g++ -O3 -o simple_heatmap_fixed algorithms/scanner_clean/simple_heatmap_fixed.cpp
        echo "✓ simple_heatmap_fixed built"
        echo ""
        echo "All builds complete!"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"