import { useState } from "react";
import axios from "axios";
import FilterPanel from "../components/FilterPanel";
import ListingCard from "../components/ListingCard";
import StatsBar from "../components/StatsBar";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [filters, setFilters] = useState({
    city: "Buffalo",
    state: "NY",
    minPrice: 50000,
    maxPrice: 500000,
    minRentYield: 0,
    minValueScore: 0,
    sortBy: "value_score",
  });
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const search = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await axios.get(`${API}/api/listings`, {
        params: {
          city: filters.city,
          state: filters.state,
          min_price: filters.minPrice,
          max_price: filters.maxPrice,
          min_rent_yield: filters.minRentYield,
          min_value_score: filters.minValueScore,
          sort_by: filters.sortBy,
        },
      });
      setListings(data.listings || []);
      setSearched(true);
    } catch (e) {
      setError("Failed to fetch listings. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🏠 DealScan</h1>
          <p className="text-xs text-gray-400">Real Estate Investment Intelligence — Powered by Zillow & Redfin</p>
        </div>
        <div className="text-xs text-gray-500 text-right">
          <div>Free • No API keys required</div>
          <div>Census + HUD rent data</div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <FilterPanel
          filters={filters}
          setFilters={setFilters}
          onSearch={search}
          loading={loading}
        />

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-4 text-red-300">
            ⚠️ {error}
          </div>
        )}

        {searched && !loading && (
          <>
            <StatsBar listings={listings} />
            {listings.length === 0 ? (
              <div className="text-center text-gray-500 py-20">
                <div className="text-5xl mb-4">🔍</div>
                <p>No listings matched your filters. Try adjusting price range or filters.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {listings.map((l, i) => (
                  <ListingCard key={l.zpid || l.address + i} listing={l} />
                ))}
              </div>
            )}
          </>
        )}

        {!searched && !loading && (
          <div className="text-center text-gray-600 py-24">
            <div className="text-6xl mb-4">🏡</div>
            <p className="text-xl font-semibold text-gray-400">Find Your Next Investment</p>
            <p className="text-gray-500 mt-2">Set your filters and click Search to discover undervalued properties</p>
          </div>
        )}
      </div>
    </div>
  );
}
