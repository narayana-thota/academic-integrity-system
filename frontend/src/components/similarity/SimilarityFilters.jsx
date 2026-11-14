export default function SimilarityFilters({
  search,
  setSearch,
  category,
  setCategory,
  action,
  setAction,
  categories,
  actions,
  onClear,
}) {
  return (
    <div className="similarity-filters">
      <div className="similarity-search">
        <span>⌕</span>
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search report ID or submission ID..."
        />
      </div>

      <select
        value={category}
        onChange={(event) => setCategory(event.target.value)}
      >
        <option value="">All report categories</option>
        {categories.map((item) => (
          <option key={item} value={item}>
            {item.replaceAll("_", " ")}
          </option>
        ))}
      </select>

      <select
        value={action}
        onChange={(event) => setAction(event.target.value)}
      >
        <option value="">All review actions</option>
        {actions.map((item) => (
          <option key={item} value={item}>
            {item.replaceAll("_", " ")}
          </option>
        ))}
      </select>

      <button className="similarity-clear" onClick={onClear}>
        Clear filters
      </button>
    </div>
  );
}