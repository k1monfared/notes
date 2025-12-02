import matplotlib.pyplot as plt
import numpy as np

# Two dice probabilities
sums = list(range(2, 13))
counts = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
probabilities = [c/36 for c in counts]
percentages = [p*100 for p in probabilities]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Bar chart
bars = ax.bar(sums, percentages, color='steelblue', edgecolor='black', linewidth=1.5)

# Add value labels on top of bars
for i, (s, pct, cnt) in enumerate(zip(sums, percentages, counts)):
    ax.text(s, pct + 0.5, f'{cnt}/36\n{pct:.1f}%', 
            ha='center', va='bottom', fontsize=9, fontweight='bold')

# Styling
ax.set_xlabel('Sum', fontsize=12, fontweight='bold')
ax.set_ylabel('Probability (%)', fontsize=12, fontweight='bold')
ax.set_title('Two Dice: Probability Distribution', fontsize=14, fontweight='bold')
ax.set_xticks(sums)
ax.set_ylim(0, max(percentages) + 3)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Save the figure
plt.tight_layout()
plt.savefig('two_dice_distribution.png', dpi=150, bbox_inches='tight')
print("Generated: two_dice_distribution.png")
