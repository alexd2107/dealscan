export default function StatsBar({ listings }) {
  if (!listings.length) return null;
  const avgPrice = Math.round(listings.reduce((a, l) => a + (l.price || 0), 0) / listings.length);
  const avgYield = (listings.reduce((a, l) => a + (l.rent_yield || 0), 0) / listings.length).toFixed(1);
  const avgScore = (listings.reduce((a, l) => a + (l.value_score || 0), 0) / listings.length).toFixed(1);
  const topDeal = listings[0];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {[
        { label: "Properties Found", value: listings.length, icon: "🏠" },
        { label: "Avg Price", value: "$" + avgPrice.toLocaleString(), icon: "💵" },
        { label: "Avg Rent Yield", value: avgYield + "%", icon: "📈" },
        { label: "Avg Value Score", value: avgScore + "/100", icon: "⚡" },
      ].map(s => (
        <div key={s.label} className="bg-gray-900 border border-gray-700 rounded-xl p-4 text-center">
          <div className="text-2xl mb-1">{s.icon}</div>
          <div className="text-xl font-bold text-white">{s.value}</div>
          <div className="text-xs text-gray-400">{s.label}</div>
        </div>
      ))}
    </div>
  );
}
