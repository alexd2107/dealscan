export default function ScoreBadge({ score }) {
  const color =
    score >= 70 ? "bg-green-700 text-green-100" :
    score >= 40 ? "bg-yellow-700 text-yellow-100" :
                  "bg-red-900 text-red-200";
  return (
    <span className={`text-xs font-bold px-2 py-1 rounded-full ${color}`}>
      ⚡ {score}
    </span>
  );
}
