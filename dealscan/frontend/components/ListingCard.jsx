import ScoreBadge from "./ScoreBadge";

export default function ListingCard({ listing }) {
  const {
    address, price, beds, baths, sqft, img, url, source,
    monthly_rent_est, rent_yield, value_gap_pct, value_score, growth_score,
    agent_name, agent_phone,
  } = listing;

  const contactAgent = () => {
    const subject = encodeURIComponent(`Investment Inquiry: ${address}`);
    const body = encodeURIComponent(
      `Hi${agent_name ? " " + agent_name : ""},\n\nI am interested in the property at ${address}, listed at $${price?.toLocaleString()}.\n\nCould you please provide more details and arrange a viewing?\n\nThank you.`
    );
    window.open(`mailto:?subject=${subject}&body=${body}`);
  };

  const callAgent = () => {
    if (agent_phone) window.open(`tel:${agent_phone}`);
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl overflow-hidden hover:border-blue-500 transition-all hover:shadow-lg hover:shadow-blue-900/30 flex flex-col">
      {img ? (
        <img src={img} alt={address} className="w-full h-44 object-cover" />
      ) : (
        <div className="w-full h-44 bg-gray-800 flex items-center justify-center text-5xl">🏠</div>
      )}

      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-start justify-between gap-2 mb-1">
          <a href={url} target="_blank" rel="noopener noreferrer"
            className="text-sm font-semibold text-white hover:text-blue-400 leading-tight">
            {address}
          </a>
          <ScoreBadge score={value_score} />
        </div>

        <p className="text-2xl font-bold text-green-400 mb-3">
          ${price?.toLocaleString()}
        </p>

        <div className="flex flex-wrap gap-1 text-xs mb-3">
          {beds > 0 && <span className="bg-gray-800 px-2 py-1 rounded">🛏 {beds} bd</span>}
          {baths > 0 && <span className="bg-gray-800 px-2 py-1 rounded">🚿 {baths} ba</span>}
          {sqft > 0 && <span className="bg-gray-800 px-2 py-1 rounded">📐 {Number(sqft).toLocaleString()} sqft</span>}
          <span className="bg-gray-800 px-2 py-1 rounded text-gray-400">{source}</span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-xs mb-4">
          <div className="bg-blue-950 rounded-lg p-2">
            <div className="text-blue-300 font-bold">{rent_yield}%</div>
            <div className="text-gray-400">Rent Yield</div>
          </div>
          <div className="bg-yellow-950 rounded-lg p-2">
            <div className="text-yellow-300 font-bold">{value_gap_pct}%</div>
            <div className="text-gray-400">Value Gap</div>
          </div>
          <div className="bg-purple-950 rounded-lg p-2">
            <div className="text-purple-300 font-bold">{growth_score}</div>
            <div className="text-gray-400">Growth</div>
          </div>
        </div>

        <div className="text-xs text-gray-400 mb-4">
          Est. Monthly Rent: <span className="text-green-400 font-semibold">${monthly_rent_est?.toLocaleString()}/mo</span>
          {agent_name && <span className="ml-3">Agent: {agent_name}</span>}
        </div>

        <div className="mt-auto flex gap-2">
          <button onClick={contactAgent}
            className="flex-1 bg-blue-600 hover:bg-blue-500 py-2 rounded-xl text-sm font-semibold transition">
            ✉️ Email Agent
          </button>
          {agent_phone && (
            <button onClick={callAgent}
              className="bg-green-700 hover:bg-green-600 px-4 py-2 rounded-xl text-sm font-semibold transition">
              📞
            </button>
          )}
          <a href={url} target="_blank" rel="noopener noreferrer"
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-xl text-sm font-semibold transition">
            🔗
          </a>
        </div>
      </div>
    </div>
  );
}
