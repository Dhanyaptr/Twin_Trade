import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type AutomaticModeResult = {
  status: string;
  message?: string; // for error responses
  best_pair?: [string, string];
  latest_signal?: string;
  hedge_ratio?: number;
  zscore?: number[];
  spread?: number[];
  correlation?: number[];
  dates?: string[];
  stock1_prices?: number[];   // NEW
  stock2_prices?: number[];
};

function AutomaticMode() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AutomaticModeResult | null>(null);

  const runAutomaticMode = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/automatic-mode");
      const data: AutomaticModeResult = await res.json();
      setResult(data);
    } catch (err) {
      console.error("Error fetching automatic mode:", err);
      setResult({ status: "error", message: "Failed to connect to backend." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Automatic Mode</h1>

      <button
        onClick={runAutomaticMode}
        className="bg-blue-600 text-white px-4 py-2 rounded shadow"
      >
        Run Automatic Mode
      </button>

      {loading && <p className="mt-4">Loading...</p>}

      {/* Show error from backend */}
      {result?.status === "error" && (
        <div className="mt-4 text-red-600 font-medium">
          {result.message || "Something went wrong."}
        </div>
      )}

      {/* Show result if ok */}
      {result?.status === "ok" && result.best_pair && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <h2 className="text-xl font-semibold">
            Best Pair: {result.best_pair[0]} & {result.best_pair[1]}
          </h2>
          

          {/* Graph Section */}
          {/* Price Movement Graph */}
          {result.dates && result.stock1_prices && result.stock2_prices && (
            <div className="p-4 border rounded bg-gray-50 mb-6">
              <h3 className="text-lg font-semibold mb-2">
                {result.best_pair[0]} vs {result.best_pair[1]} Price Movement
              </h3>
              <div style={{ width: "100%", height: 400 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={result.dates.map((date, i) => ({
                      date,
                      [result.best_pair?.[0] || "Stock1"]: result.stock1_prices?.[i],
                      [result.best_pair?.[1] || "Stock2"]: result.stock2_prices?.[i],
                    }))}
                  >
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey={result.best_pair?.[0] || "Stock1"}
                      stroke="#0000ff"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey={result.best_pair?.[1] || "Stock2"}
                      stroke="#ff0000"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Correlation Graph */}
          {result.dates && result.correlation && (
            <div className="p-4 border rounded bg-gray-50 mb-6">
              <h3 className="text-lg font-semibold mb-2">Rolling Correlation</h3>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={result.dates.map((date, i) => ({
                      date,
                      correlation: result.correlation?.[i],
                    }))}
                  >
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[-1, 1]} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="correlation"
                      stroke="#ff7300"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {/* Graph Section */}
          {result.dates && result.zscore && result.spread && (
            <div style={{ width: "100%", height: 400, marginTop: 20 }}>
              <ResponsiveContainer>
                <LineChart
                  data={result.dates.map((date, i) => ({
                    date,
                    zscore: result.zscore?.[i],
                    spread: result.spread?.[i],
                  }))}
                >
                  <XAxis dataKey="date" hide />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="zscore"
                    stroke="#8884d8"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="spread"
                    stroke="#82ca9d"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        

          <p className="mt-2">Latest Signal: {result.latest_signal}</p>
          <p>
            Hedge Ratio:{" "}
            {result.hedge_ratio !== undefined
              ? result.hedge_ratio.toFixed(4)
              : "N/A"}
          </p>
        </div>
      )}
    </div>
  );
}

export default AutomaticMode;
