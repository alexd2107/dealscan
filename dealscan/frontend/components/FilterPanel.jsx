export default function FilterPanel({ filters, setFilters, onSearch, loading }) {
  const states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY",
    "NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl p-5 mb-6">
      <h2 className="text-lg font-semibold text-gray-200 mb-4">🔍 Search Filters</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">

        <div className="col-span-2 md:col-span-1">
          <label className="text-xs text-gray-400 uppercase tracking-wider">City</label>
          <input
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            placeholder="e.g. Buffalo"
            value={filters.city}
            onChange={e => setFilters({ ...filters, city: e.target.value })}
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">State</label>
          <select
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.state}
            onChange={e => setFilters({ ...filters, state: e.target.value })}
          >
            {states.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">Min Price ($)</label>
          <input type="number" step="10000"
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.minPrice}
            onChange={e => setFilters({ ...filters, minPrice: +e.target.value })}
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">Max Price ($)</label>
          <input type="number" step="10000"
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.maxPrice}
            onChange={e => setFilters({ ...filters, maxPrice: +e.target.value })}
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">Min Rent Yield (%)</label>
          <input type="number" step="0.5" min="0"
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.minRentYield}
            onChange={e => setFilters({ ...filters, minRentYield: +e.target.value })}
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">Min Value Score</label>
          <input type="number" step="1" min="0" max="100"
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.minValueScore}
            onChange={e => setFilters({ ...filters, minValueScore: +e.target.value })}
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider">Sort By</label>
          <select
            className="mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            value={filters.sortBy}
            onChange={e => setFilters({ ...filters, sortBy: e.target.value })}
          >
            <option value="value_score">Best Value Score</option>
            <option value="price">Price: Low to High</option>
            <option value="rent_yield">Highest Rent Yield</option>
          </select>
        </div>

      </div>
      <button
        onClick={onSearch}
        disabled={loading}
        className="mt-5 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed py-3 rounded-xl font-bold text-lg transition"
      >
        {loading ? "⏳ Searching..." : "🔍 Find Deals"}
      </button>
    </div>
  )
}
