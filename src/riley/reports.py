"""Report skeleton generation for Riley Project"""
from pathlib import Path
from typing import List, Dict, Any
import json


def generate_skeleton_report(symbol: str, as_of_date: str,
                             packet_dir: Path, output_path: Path) -> Path:
    """
    Generate a Markdown skeleton report with factual data only.

    Analyst will fill in TBD sections later.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load packet files
    with open(packet_dir / 'context.json', 'r') as f:
        context = json.load(f)

    with open(packet_dir / 'levels.json', 'r') as f:
        levels_data = json.load(f)

    with open(packet_dir / 'diff.json', 'r') as f:
        diff = json.load(f)

    with open(packet_dir / 'packet.json', 'r') as f:
        packet = json.load(f)

    # Build skeleton markdown
    md = []
    md.append(f"# {symbol} Trading Analysis - {as_of_date}")
    md.append("")
    md.append("---")
    md.append("")

    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    md.append("**TBD** - Analyst to complete")
    md.append("")

    # Narrative
    md.append("## Narrative")
    md.append("")
    md.append("**TBD** - Analyst to complete")
    md.append("")

    # Time Context
    md.append("## Time Context")
    md.append("")
    cycle_status = packet.get('cycles', {}).get('status', 'missing')
    if cycle_status == 'missing':
        md.append("**Cycle pack missing** - No cycle data available for this instrument.")
    else:
        md.append("**Cycles loaded:**")
        md.append(f"```json")
        md.append(json.dumps(packet['cycles'], indent=2))
        md.append("```")
    md.append("")

    # Levels
    md.append("## Key Levels")
    md.append("")
    md.append("| Tier | Label | Price | Source |")
    md.append("|------|-------|-------|--------|")

    for level in levels_data['levels']:
        tier = level['tier']
        label = level['label']
        price = f"{level['level_price']:.2f}"
        source = level['source']
        md.append(f"| {tier} | {label} | {price} | {source} |")

    md.append("")

    # Triggers
    md.append("## Triggers")
    md.append("")
    md.append("**TBD** - Analyst to complete")
    md.append("")

    # Plan A / Plan B / WAIT
    md.append("## Trading Plans")
    md.append("")
    md.append("### Plan A")
    md.append("**TBD** - Analyst to complete")
    md.append("")
    md.append("### Plan B")
    md.append("**TBD** - Analyst to complete")
    md.append("")
    md.append("### WAIT Scenario")
    md.append("**TBD** - Analyst to complete")
    md.append("")

    # What Changed
    md.append("## What Changed Since Yesterday")
    md.append("")
    if diff['status'] == 'no_previous_run':
        md.append("*First run - no previous data for comparison*")
    else:
        if diff['price_change']:
            md.append(f"- **Price Change:** {diff['price_change']}")
        if diff['new_pivots']:
            md.append(f"- **New Pivots:** {len(diff['new_pivots'])}")
        if diff['level_changes']:
            md.append(f"- **Level Changes:** {len(diff['level_changes'])}")
    md.append("")

    # Market Context
    md.append("## Market Context")
    md.append("")
    md.append(f"**Volatility Regime:** {context['volatility_regime']['regime']} "
              f"(ATR Percentile: {context['volatility_regime']['percentile']:.1f})")
    md.append("")
    md.append(f"**Trend Regime:** {context['trend_regime']['regime']}")
    md.append("")

    # Footer
    md.append("---")
    md.append("")
    md.append(f"*Generated: {as_of_date}*  ")
    md.append(f"*Data Coverage: {context['timeframe_coverage']['start']} to {context['timeframe_coverage']['end']}*")

    # Write file
    content = "\n".join(md)
    with open(output_path, 'w') as f:
        f.write(content)

    print(f"Skeleton report written: {output_path}")
    return output_path
