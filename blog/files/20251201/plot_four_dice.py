import matplotlib.pyplot as plt
import numpy as np

# Four dice probabilities
sums = list(range(2, 13))
counts = [171, 302, 461, 580, 727, 834, 727, 580, 461, 302, 171]
probabilities = [c/1296 for c in counts]
percentages = [p*100 for p in probabilities]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Bar chart
bars = ax.bar(sums, percentages, color='coral', edgecolor='black', linewidth=1.5)

# Add value labels on top of bars
for i, (s, pct, cnt) in enumerate(zip(sums, percentages, counts)):
    ax.text(s, pct + 1, f'{cnt}/1296\n{pct:.1f}%', 
            ha='center', va='bottom', fontsize=9, fontweight='bold')

# Styling
ax.set_xlabel('Sum', fontsize=12, fontweight='bold')
ax.set_ylabel('Probability (%)', fontsize=12, fontweight='bold')
ax.set_title('Four Dice: P(at least one pair sums to x)', fontsize=14, fontweight='bold')
ax.set_xticks(sums)
ax.set_ylim(0, max(percentages) + 8)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Save the figure
plt.tight_layout()
plt.savefig('four_dice_distribution.png', dpi=150, bbox_inches='tight')
print("Generated: four_dice_distribution.png")
