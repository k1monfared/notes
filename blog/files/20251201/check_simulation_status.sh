#!/bin/bash
# Simulation Status Checker

LOG_FILE="benchmark_enhanced.log"
RESULTS_DIR="results"

echo "================================================================================================"
echo "CAN'T STOP SIMULATION STATUS"
echo "================================================================================================"
echo ""

# Check if simulation is running
if pgrep -f "comprehensive_benchmark_enhanced.py" > /dev/null; then
    echo "✓ Simulation is RUNNING"
    PID=$(pgrep -f "comprehensive_benchmark_enhanced.py")
    echo "  PID: $PID"
else
    echo "✗ Simulation is NOT running"
fi

echo ""
echo "================================================================================================"
echo "PROGRESS"
echo "================================================================================================"
echo ""

# Single-player progress
SP_DONE=$(grep -c "Done in" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Single-player completed: $SP_DONE / 38 strategies"

# Head-to-head progress
H2H_DONE=$(grep -c "^\[.*\].*vs.*-.*(" "$LOG_FILE" 2>/dev/null || echo "0")
H2H_TOTAL=1444
echo "Head-to-head completed: $H2H_DONE / $H2H_TOTAL matchups"

echo ""
echo "================================================================================================"
echo "OUTPUT FILES (Current Size)"
echo "================================================================================================"
echo ""

# Check for result files
if [ -d "$RESULTS_DIR" ]; then
    # Single-player files
    SP_RAW=$(ls -lh "$RESULTS_DIR"/single_player_raw_*.jsonl.gz 2>/dev/null | awk '{print $5}' | head -1)
    SP_STATS=$(ls -lh "$RESULTS_DIR"/single_player_stats_*.json 2>/dev/null | awk '{print $5}' | head -1)

    # Head-to-head files
    H2H_RAW=$(ls -lh "$RESULTS_DIR"/head_to_head_raw_*.jsonl.gz 2>/dev/null | awk '{print $5}' | head -1)
    H2H_STATS=$(ls -lh "$RESULTS_DIR"/head_to_head_stats_*.json 2>/dev/null | awk '{print $5}' | head -1)

    # Summary
    SUMMARY=$(ls -lh "$RESULTS_DIR"/summary_report_*.md 2>/dev/null | awk '{print $5}' | head -1)

    echo "Single-player raw data:    ${SP_RAW:-not yet created} (target: ~3.4 MB)"
    echo "Single-player stats:       ${SP_STATS:-not yet created} (target: ~500 KB)"
    echo "Head-to-head raw data:     ${H2H_RAW:-not yet created} (target: ~174 MB)"
    echo "Head-to-head stats:        ${H2H_STATS:-not yet created} (target: ~2 MB)"
    echo "Summary report:            ${SUMMARY:-not yet created}"

    # Total size
    TOTAL_SIZE=$(du -sh "$RESULTS_DIR" 2>/dev/null | awk '{print $1}')
    echo ""
    echo "Total results directory:   ${TOTAL_SIZE:-0}"
else
    echo "Results directory not yet created"
fi

# Check for completion marker
if ls "$RESULTS_DIR"/SIMULATION_COMPLETE_* 2>/dev/null | grep -q .; then
    echo ""
    echo "🎉 SIMULATION COMPLETE!"
    cat "$RESULTS_DIR"/SIMULATION_COMPLETE_*
else
    # Estimate time remaining based on progress
    if [ "$H2H_DONE" -gt 0 ] 2>/dev/null; then
        START_TIME=$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo "0")
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))

        if [ "$ELAPSED" -gt 0 ] && [ "$H2H_DONE" -gt 0 ]; then
            TIME_PER_MATCHUP=$((ELAPSED / H2H_DONE))
            REMAINING_MATCHUPS=$((H2H_TOTAL - H2H_DONE))
            ESTIMATED_REMAINING=$((TIME_PER_MATCHUP * REMAINING_MATCHUPS))

            echo ""
            echo "Estimated time remaining: $((ESTIMATED_REMAINING / 3600)) hours $((ESTIMATED_REMAINING % 3600 / 60)) minutes"
        fi
    fi
fi

echo ""
echo "================================================================================================"
echo "RECENT ACTIVITY (last 10 lines)"
echo "================================================================================================"
tail -10 "$LOG_FILE" 2>/dev/null | grep -v "playable\|Active runners\|Applying\|Result:" || echo "No recent activity"

echo ""
echo "================================================================================================"
echo "COMMANDS"
echo "================================================================================================"
echo "Monitor live:     tail -f $LOG_FILE"
echo "View progress:    grep 'Testing\|Done in' $LOG_FILE | tail -20"
echo "Check completion: ls -lh $RESULTS_DIR/SIMULATION_COMPLETE_*"
echo "================================================================================================"
