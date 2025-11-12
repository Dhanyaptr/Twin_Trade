import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import {
  LogOut,
  TrendingUp,
  BarChart3,
  Activity,
  Zap,
  Settings,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

type AutomaticModeResult = {
  trade_action: string;
  status?: string;
  message?: string;
  best_pair?: [string, string];
  latest_signal?: string;
  hedge_ratio?: number;
  zscore?: number[];
  spread?: number[];
  correlation?: number[];
  dates?: string[];
  stock1_prices?: number[];
  stock2_prices?: number[];
  latest_recommendation?: Record<string, string>; // ✅ add this line
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [selectedStockA, setSelectedStockA] = useState("");
  // stockB removed on purpose
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const userEmail = localStorage.getItem("userEmail") || "user@example.com";
  const [autoResult, setAutoResult] = useState<AutomaticModeResult | null>(
    null
  );

  // NEW: custom result state
  const [customResult, setCustomResult] = useState<AutomaticModeResult | null>(
    null
  );

  useEffect(() => {
    const fetchAutoData = async () => {
      try {
        const response = await fetch("http://localhost:8000/automatic-mode");
        const data: AutomaticModeResult = await response.json();
        setAutoResult(data);
      } catch (error) {
        console.error("Error fetching automatic mode result:", error);
      }
    };

    fetchAutoData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("userEmail");
    toast({
      title: "Logged out successfully",
      description: "See you next time!",
    });
    navigate("/signin");
  };

  // ---------- NEW: Custom Mode handler (single-stock) ----------
  const handleCustomAnalysis = async () => {
    if (!selectedStockA) {
      toast({
        title: "Please select a stock",
        description: "Stock A is required for analysis.",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    setCustomResult(null);

    try {
      // call backend POST /custom-mode with selected stock
      const resp = await fetch("http://localhost:8000/custom-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stock: selectedStockA }),
      });

      const data = await resp.json();

      if (!resp.ok) {
        toast({
          title: "Analysis failed",
          description:
            data?.message || data?.error || "Server returned an error",
          variant: "destructive",
        });
        setIsAnalyzing(false);
        return;
      }

      // Normalize backend response to match chart expectations
      const mapped = {
        ...data,
        best_pair: [data.selected_stock, data.pair_stock], // build the pair
        stock1_prices: data.stock1_prices,
        stock2_prices: data.stock2_prices,
        zscore: data.zscore,
        spread: data.spread,
        rolling_mean: data.rolling_mean,
        correlation: data.correlation,
        dates: data.dates,
      };

      setCustomResult(mapped);

      toast({
        title: "Analysis complete",
        description: `Best pair found for ${selectedStockA}: ${mapped.best_pair.join(
          " - "
        )}`,
      });
    } catch (err) {
      console.error("Custom analysis error", err);
      toast({
        title: "Network error",
        description: "Could not reach backend. Check server and try again.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Helper: compute actions per index from zscore
  // Based on conventional pair-trading signals:
  // z > +2 => SELL stockA, BUY pairStock
  // z < -2 => BUY stockA, SELL pairStock
  // else => HOLD
  const computeActions = (zscoreArr?: number[]) => {
    if (!zscoreArr) return [];
    return zscoreArr.map((z) => {
      if (z > 2) return { actionA: "SELL", actionB: "BUY", z };
      if (z < -2) return { actionA: "BUY", actionB: "SELL", z };
      return { actionA: "HOLD", actionB: "HOLD", z };
    });
  };

  // Build series for recharts from arrays
  const buildSeries = (res?: AutomaticModeResult) => {
    if (!res || !res.dates) return [];
    const n = res.dates.length;
    const s1 = res.stock1_prices ?? [];
    const s2 = res.stock2_prices ?? [];
    const z = res.zscore ?? [];
    const sp = res.spread ?? [];
    const rm = res.rolling_mean ?? [];
    const corr = res.correlation ?? [];

    // --- 🔧 Normalize both series so they move together ---
    // Use actual prices (no normalization) for stock1 and stock2
    const s1Norm = s1; // or remove s1Norm entirely
    const s2Norm = s2; // or remove s2Norm entirely

    const actions = computeActions(z);

    const data = [];
    for (let i = 0; i < n; i++) {
      data.push({
        date: res.dates[i],
        stock1: s1[i] ?? null, // actual price
        stock2: s2[i] ?? null,
        zscore: z[i] ?? null,
        spread: sp[i] ?? null,
        rolling_mean: rm[i] ?? null,
        correlation: corr[i] ?? null,
        actionA: actions[i]?.actionA ?? "HOLD",
        actionB: actions[i]?.actionB ?? "HOLD",
      });
    }
    return data;
  };

  const stockOptions = [
    "3IINFOLTD",
    "AURIONPRO",
    "BSOFT",
    "COFORGE",
    "CYIENT",
    "DATAMATICS",
    "HAPPSTMNDS",
    "HCLTECH",
    "INFY",
    "INTELLECT",
    "KPITTECH",
    "LTIM",
    "LTTS",
    "NEWGEN",
    "NIITLTD",
    "NUCLEUS",
    "OFSS",
    "PERSISTENT",
    "SASKEN",
    "SONATSOFTW",
    "TANLA",
    "TATAELXSI",
    "TCS",
    "TECHM",
    "WIPRO",
    "XCHANGING",
    "ZENSARTECH",
  ];

  // ---------- Render ----------
  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Navigation Bar */}
      <nav className="bg-card shadow-card border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                TwinTrade
              </h1>
              <div className="hidden md:flex space-x-6">
                <span className="text-primary font-medium border-b-2 border-primary pb-1">
                  Dashboard
                </span>
                {/* <span className="text-muted-foreground hover:text-foreground cursor-pointer transition-smooth">
                  Profile
                </span> */}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground hidden sm:block">
                {userEmail}
              </span>
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-foreground mb-2">
            Trading Dashboard
          </h2>
          <p className="text-muted-foreground">
            Monitor your pair trading strategies and analyze market
            opportunities
          </p>
        </div>

        <Tabs defaultValue="automatic" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger
              value="automatic"
              className="flex items-center space-x-2"
            >
              <Zap className="h-4 w-4" />
              <span>Automatic Mode</span>
            </TabsTrigger>
            <TabsTrigger value="custom" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>Custom Mode</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="automatic" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
              {/* Best Cointegrated Pair */}
              <Card className="shadow-card hover:shadow-elegant transition-smooth">
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div>
                    <CardTitle className="text-lg">
                      Best Cointegrated Pair
                    </CardTitle>
                    <CardDescription>
                      Highest correlation pair today
                    </CardDescription>
                  </div>
                  <TrendingUp className="h-6 w-6 text-success ml-auto" />
                </CardHeader>
                <CardContent>
                  {autoResult ? (
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">
                          {autoResult.best_pair?.join(" - ") || "N/A"}
                        </span>
                        <span className="text-success font-semibold">
                          {autoResult.spread
                            ? `${(autoResult.spread.slice(-1)[0] ?? 0).toFixed(
                                2
                              )}%`
                            : ""}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Correlation:{" "}
                        {autoResult.correlation?.slice(-1)[0]?.toFixed(2) ??
                          "N/A"}{" "}
                        | Z-Score:{" "}
                        {autoResult.zscore?.slice(-1)[0]?.toFixed(2) ?? "N/A"}
                      </div>
                      <div className="w-full bg-muted h-2 rounded-full">
                        <div
                          className="bg-success h-2 rounded-full"
                          style={{
                            width: `${
                              (autoResult.correlation?.slice(-1)[0] ?? 0) * 100
                            }%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">Loading...</p>
                  )}
                </CardContent>
              </Card>

              {/* Correlation Matrix */}
              <Card className="shadow-card hover:shadow-elegant transition-smooth">
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div>
                    <CardTitle className="text-lg">Price Movement</CardTitle>
                    <CardDescription>
                      Real-time correlation graph
                    </CardDescription>
                  </div>
                  <BarChart3 className="h-6 w-6 text-primary ml-auto" />
                </CardHeader>
                <CardContent>
                  {autoResult &&
                  autoResult.dates &&
                  autoResult.stock1_prices &&
                  autoResult.stock2_prices ? (
                    <div style={{ width: "100%", height: 380 }}>
                      <ResponsiveContainer>
                        <LineChart
                          data={autoResult.dates.map((date, i) => {
                            const s1 = autoResult.stock1_prices?.[i] ?? 0;
                            const s2 = autoResult.stock2_prices?.[i] ?? 0;

                            return {
                              date,
                              [autoResult.best_pair?.[0] || "Stock1"]: s1,
                              [autoResult.best_pair?.[1] || "Stock2"]: s2,
                            };
                          })}
                          margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
                        >
                          <XAxis
                            dataKey="date"
                            tick={{ fontSize: 9 }}
                            angle={-45}
                            textAnchor="end"
                            interval="preserveStartEnd"
                            height={60} // prevents company names from drifting upward
                            label={{
                              value: "Date", // <-- X-axis title
                              position: "insideBottom", // places it neatly below tick labels
                              offset: -4, // adjusts vertical spacing (tweak as needed)
                              style: {
                                textAnchor: "middle",
                                fontWeight: "bold", // bold text
                                fill: "#000000",
                              },
                            }}
                          />
                          <YAxis
                            tick={{ fontSize: 12 }}
                            label={{
                              value: "Price (₹)",
                              angle: -90,
                              position: "insideLeft",
                              style: {
                                textAnchor: "middle",
                                fontWeight: "bold", // bold text
                                fill: "#000000",
                              },
                            }}
                          />

                          <Tooltip />
                          <Legend />

                          {/* Lines */}
                          <Line
                            type="monotone"
                            dataKey={autoResult.best_pair?.[0] || "Stock1"}
                            stroke="#2563eb"
                            dot={false}
                            isAnimationActive={false}
                          />
                          <Line
                            type="monotone"
                            dataKey={autoResult.best_pair?.[1] || "Stock2"}
                            stroke="#ef4444"
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">Loading...</p>
                  )}
                </CardContent>
              </Card>

              {/* Rolling Z-score Plot */}
              <Card className="shadow-card hover:shadow-elegant transition-smooth">
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div>
                    <CardTitle className="text-lg">Rolling Z-Score</CardTitle>
                    <CardDescription>
                      Price spread normalization
                    </CardDescription>
                  </div>
                  <Activity className="h-6 w-6 text-accent ml-auto" />
                </CardHeader>
                <CardContent>
                  {autoResult ? (
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span>Current Z-Score:</span>
                        <span
                          className={`font-semibold ${
                            (autoResult.zscore?.slice(-1)[0] ?? 0) > 2
                              ? "text-destructive"
                              : (autoResult.zscore?.slice(-1)[0] ?? 0) < -2
                              ? "text-success"
                              : "text-warning"
                          }`}
                        >
                          {autoResult.zscore?.slice(-1)[0]?.toFixed(2) ?? "N/A"}
                        </span>
                      </div>
                      <div className="relative w-full h-4 bg-muted rounded-full overflow-hidden">
                        {/* Center line */}
                        <div className="absolute left-1/2 top-0 h-full w-0.5 bg-foreground/30 z-10"></div>

                        {/* Z-score fill bar */}
                        <div
                          className={`absolute top-0 h-full rounded-full transition-all duration-500 ${
                            (autoResult.zscore?.slice(-1)[0] ?? 0) > 2
                              ? "bg-destructive"
                              : (autoResult.zscore?.slice(-1)[0] ?? 0) < -2
                              ? "bg-success"
                              : "bg-warning"
                          }`}
                          style={{
                            left: "50%",
                            width: `${Math.min(
                              Math.abs(
                                ((autoResult.zscore?.slice(-1)[0] ?? 0) / 4) *
                                  100
                              ),
                              50
                            )}%`,
                            transform:
                              (autoResult.zscore?.slice(-1)[0] ?? 0) < 0
                                ? "translateX(-100%)"
                                : "translateX(0)",
                          }}
                        ></div>
                      </div>

                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>-2.0</span>
                        <span>0</span>
                        <span>+2.0</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">Loading...</p>
                  )}
                </CardContent>
              </Card>

              {/* Trading Signals */}
              <Card className="shadow-card hover:shadow-elegant transition-smooth">
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div>
                    <CardTitle className="text-lg">Trading Signals</CardTitle>
                    <CardDescription>Active recommendations</CardDescription>
                  </div>
                  <TrendingUp className="h-6 w-6 text-primary ml-auto" />
                </CardHeader>
                <CardContent>
                  {autoResult ? (
                    <div className="space-y-3">
                      <div
                        className={`flex items-center justify-between p-2 rounded ${
                          autoResult.latest_signal === "BUY"
                            ? "bg-success/10 text-success"
                            : autoResult.latest_signal === "SELL"
                            ? "bg-destructive/10 text-destructive"
                            : "bg-warning/10 text-warning"
                        }`}
                      >
                        <span className="text-sm font-medium">
                          {autoResult.trade_action || "No trade suggestion"}
                        </span>
                        <span className="text-xs px-2 py-1 rounded border">
                          Hedge Ratio:{" "}
                          {autoResult.hedge_ratio?.toFixed(2) ?? "N/A"}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Spread:{" "}
                        {autoResult.spread?.slice(-1)[0]?.toFixed(2) ?? "N/A"}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Updated just now
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">Loading...</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ----------------- CUSTOM MODE (ONLY STOCK A) ----------------- */}
          <TabsContent value="custom" className="space-y-6">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Custom Pair Analysis</span>
                </CardTitle>
                <CardDescription>
                  Select one stock — system will find the best pair
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Stock selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Stock (A)</label>
                    <Select
                      value={selectedStockA}
                      onValueChange={setSelectedStockA}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select stock" />
                      </SelectTrigger>
                      <SelectContent>
                        {stockOptions.map((stock) => (
                          <SelectItem key={stock} value={stock}>
                            {stock}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Run analysis button */}
                <Button
                  variant="gradient"
                  onClick={handleCustomAnalysis}
                  disabled={isAnalyzing || !selectedStockA}
                  className="w-full md:w-auto"
                >
                  {isAnalyzing ? "Running Analysis..." : "Run Analysis"}
                </Button>

                {/* Results: charts and recommendations */}
                {customResult ? (
                  (() => {
                    const series = buildSeries(customResult);
                    const pairName =
                      customResult.best_pair?.join(" - ") ??
                      `${selectedStockA} - Pair`;

                    return (
                      <div className="space-y-6">
                        {/* Pair info and recommendation */}
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-lg font-semibold">
                              Best Pair: {pairName}
                            </h3>
                            <div className="text-sm text-muted-foreground">
                              Hedge ratio:{" "}
                              {customResult.hedge_ratio?.toFixed(3) ?? "N/A"} •
                              P-value: {customResult.pvalue ?? "N/A"}
                            </div>
                          </div>

                          <div className="text-right">
                            <div className="text-sm font-medium text-muted-foreground mb-1">
                              Latest Recommendation
                            </div>
                            {customResult.latest_recommendation ? (
                              <div className="flex justify-end flex-wrap gap-2 mt-1">
                                {Object.entries(
                                  customResult.latest_recommendation
                                ).map(([symbol, action]) => (
                                  <span
                                    key={symbol}
                                    className={`px-3 py-1 rounded font-semibold ${
                                      action === "BUY"
                                        ? "bg-success/10 text-success"
                                        : action === "SELL"
                                        ? "bg-destructive/10 text-destructive"
                                        : "bg-muted text-muted-foreground"
                                    }`}
                                  >
                                    {symbol}: {action}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <div className="text-sm text-muted-foreground">
                                No active signal
                              </div>
                            )}
                          </div>
                        </div>

                        {/* --- Charts Section --- */}

                        {/* 1️⃣ Price Chart with Buy/Sell markers */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Price Comparison</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div style={{ width: "100%", height: 320 }}>
                              <ResponsiveContainer>
                                <LineChart
                                  data={series}
                                  margin={{
                                    top: 10,
                                    right: 20,
                                    left: 0,
                                    bottom: 0,
                                  }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" />
                                  <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 9 }}
                                    angle={-45}
                                    textAnchor="end"
                                    interval="preserveStartEnd"
                                    height={60}
                                    label={{
                                      value: "Date",
                                      position: "insideBottom",
                                      offset: -4,
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />
                                  <YAxis
                                    tick={{ fontSize: 12 }}
                                    label={{
                                      value: "Price (₹)",
                                      angle: -90,
                                      position: "insideLeft",
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />
                                  <Tooltip />
                                  <Legend />
                                  <Line
                                    type="monotone"
                                    dataKey="stock1"
                                    name={selectedStockA}
                                    stroke="#2563eb"
                                    dot={false}
                                  />
                                  <Line
                                    type="monotone"
                                    dataKey="stock2"
                                    name={customResult.best_pair?.[1] ?? "PAIR"}
                                    stroke="#ef4444"
                                    dot={false}
                                  />
                                  {/* Markers for buy/sell */}
                                  {series.map((d, i) => {
                                    const x = d.date;
                                    const yA = d.stock1;
                                    const yB = d.stock2;
                                    const markers = [];
                                    if (d.actionA === "BUY")
                                      markers.push(
                                        <ReferenceDot
                                          key={`A-buy-${i}`}
                                          x={x}
                                          y={yA}
                                          r={4}
                                          stroke="green"
                                          fill="green"
                                        />
                                      );
                                    else if (d.actionA === "SELL")
                                      markers.push(
                                        <ReferenceDot
                                          key={`A-sell-${i}`}
                                          x={x}
                                          y={yA}
                                          r={4}
                                          stroke="red"
                                          fill="red"
                                        />
                                      );
                                    if (d.actionB === "BUY")
                                      markers.push(
                                        <ReferenceDot
                                          key={`B-buy-${i}`}
                                          x={x}
                                          y={yB}
                                          r={4}
                                          stroke="green"
                                          fill="green"
                                        />
                                      );
                                    else if (d.actionB === "SELL")
                                      markers.push(
                                        <ReferenceDot
                                          key={`B-sell-${i}`}
                                          x={x}
                                          y={yB}
                                          r={4}
                                          stroke="red"
                                          fill="red"
                                        />
                                      );
                                    return markers;
                                  })}
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </CardContent>
                        </Card>

                        {/* 2️⃣ Z-score and Spread */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Z-Score & Spread</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div style={{ width: "100%", height: 260 }}>
                              <ResponsiveContainer>
                                <LineChart data={series}>
                                  <CartesianGrid strokeDasharray="3 3" />
                                  <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 9 }}
                                    angle={-45}
                                    textAnchor="end"
                                    interval="preserveStartEnd"
                                    height={60}
                                    label={{
                                      value: "Date",
                                      position: "insideBottom",
                                      offset: -4,
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />

                                  <YAxis
                                    yAxisId="left"
                                    orientation="left"
                                    tick={{ fontSize: 10 }}
                                    label={{
                                      value: "Spread (₹)",
                                      angle: -90,
                                      position: "insideLeft",
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />

                                  <YAxis yAxisId="right" orientation="right" />
                                  <Tooltip />
                                  <Legend />
                                  <Line
                                    type="monotone"
                                    dataKey="spread"
                                    name="Spread"
                                    stroke="#ef4444"
                                    dot={false}
                                    yAxisId="left"
                                  />
                                  <Line
                                    type="monotone"
                                    dataKey="zscore"
                                    name="Z-Score"
                                    stroke="#7c3aed"
                                    dot={false}
                                    yAxisId="right"
                                  />
                                  <ReferenceLine
                                    y={2}
                                    stroke="gray"
                                    strokeDasharray="3 3"
                                    yAxisId="right"
                                  />
                                  <ReferenceLine
                                    y={-2}
                                    stroke="gray"
                                    strokeDasharray="3 3"
                                    yAxisId="right"
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </CardContent>
                        </Card>

                        {/* 3️⃣ Rolling Mean */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Rolling Mean (Spread)</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div style={{ width: "100%", height: 260 }}>
                              <ResponsiveContainer>
                                <LineChart data={series}>
                                  <CartesianGrid strokeDasharray="3 3" />
                                  <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 9 }}
                                    angle={-45}
                                    textAnchor="end"
                                    interval="preserveStartEnd"
                                    height={60}
                                    label={{
                                      value: "Date",
                                      position: "insideBottom",
                                      offset: -4,
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />

                                  {/* Y-Axis */}
                                  <YAxis
                                    tick={{ fontSize: 11 }}
                                    label={{
                                      value: "Spread Value (₹)",
                                      angle: -90,
                                      position: "insideLeft",
                                      style: {
                                        textAnchor: "middle",
                                        fontWeight: "bold",
                                        fill: "#000000",
                                      },
                                    }}
                                  />
                                  <Tooltip />
                                  <Legend />
                                  <Line
                                    type="monotone"
                                    dataKey="rolling_mean"
                                    name="Rolling Mean"
                                    stroke="#059669"
                                    dot={false}
                                  />
                                  <Line
                                    type="monotone"
                                    dataKey="spread"
                                    name="Spread"
                                    stroke="#ef4444"
                                    dot={false}
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </CardContent>
                        </Card>

                        {/* 4️⃣ Rolling Correlation */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Rolling Correlation</CardTitle>
                          </CardHeader>
                          <CardContent>
                            {customResult.correlation ? (
                              <div style={{ width: "100%", height: 200 }}>
                                <ResponsiveContainer>
                                  <LineChart data={series}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                      dataKey="date"
                                      tick={{ fontSize: 9 }}
                                      angle={-45}
                                      textAnchor="end"
                                      interval="preserveStartEnd"
                                      height={60}
                                      label={{
                                        value: "Date",
                                        position: "insideBottom",
                                        offset: -4,
                                        style: {
                                          textAnchor: "middle",
                                          fontWeight: "bold",
                                          fill: "#000000",
                                        },
                                      }}
                                    />

                                    <YAxis
                                      domain={[-1, 1]} // correlation range
                                      tick={{ fontSize: 11 }}
                                      tickFormatter={(value) =>
                                        value.toFixed(2)
                                      } // ✅ round to 2 decimal places
                                      label={{
                                        value: "Correlation",
                                        angle: -90,
                                        position: "outsideLeft",
                                        offset: 60,
                                        style: {
                                          textAnchor: "middle",
                                          fontWeight: "bold",
                                          fill: "#000000",
                                        },
                                      }}
                                    />

                                    <Tooltip />
                                    <Legend />
                                    <Line
                                      type="monotone"
                                      dataKey="correlation"
                                      name="Correlation"
                                      stroke="#2563eb"
                                      dot={false}
                                    />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            ) : (
                              <p className="text-muted-foreground">
                                Correlation data not available
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      </div>
                    );
                  })()
                ) : (
                  <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
                    <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-muted-foreground mb-2">
                      Analysis Results
                    </h3>
                    <p className="text-muted-foreground">
                      {selectedStockA
                        ? `Click "Run Analysis" to generate insights for ${selectedStockA} and its best cointegrated pair.`
                        : "Select a stock and run analysis to see detailed results, charts, and trading recommendations here."}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Dashboard;
