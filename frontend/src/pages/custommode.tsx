import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BarChart3 } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Example: Replace with your ~50 IT stocks list
const stockList = [
  "INFY", "TCS", "WIPRO", "HCLTECH", "TECHM", "LTIM",
];

export default function CustomMode() {
  const [selectedStockA, setSelectedStockA] = useState("");
  const [selectedStockB, setSelectedStockB] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleRunAnalysis = () => {
    if (!selectedStockA || !selectedStockB) {
      toast({
        title: "Missing selection",
        description: "Please select both Stock A and Stock B.",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    setResults(null);

    fetch(
      `http://localhost:8000/custom-mode?stock_a=${selectedStockA}&stock_b=${selectedStockB}`
    )
      .then((res) => {
        if (!res.ok) throw new Error("Network error");
        return res.json();
      })
      .then((data) => {
        setIsAnalyzing(false);
        if (data.status === "ok") {
          setResults(data);
          toast({
            title: "Analysis complete",
            description: `Pair analysis for ${selectedStockA}-${selectedStockB} completed.`,
          });
        } else {
          toast({
            title: "Error",
            description: data.message || "Unable to analyze selected stocks.",
            variant: "destructive",
          });
        }
      })
      .catch((err) => {
        console.error("Custom analysis error:", err);
        setIsAnalyzing(false);
        toast({
          title: "Error",
          description: "Something went wrong while fetching results.",
          variant: "destructive",
        });
      });
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Custom Mode</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Stock selectors */}
          <div className="flex gap-4">
            <div className="w-1/2">
              <Select onValueChange={setSelectedStockA}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Stock A" />
                </SelectTrigger>
                <SelectContent>
                  {stockList.map((stock) => (
                    <SelectItem key={stock} value={stock}>
                      {stock}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-1/2">
              <Select onValueChange={setSelectedStockB}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Stock B" />
                </SelectTrigger>
                <SelectContent>
                  {stockList.map((stock) => (
                    <SelectItem key={stock} value={stock}>
                      {stock}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Run Analysis Button */}
          <Button onClick={handleRunAnalysis} disabled={isAnalyzing}>
            {isAnalyzing ? "Analyzing..." : "Run Analysis"}
          </Button>

          {/* Results */}
          <div className="mt-6">
            {results && results.best_pair ? (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">
                  Best Pair: {results.best_pair[0]} & {results.best_pair[1]}
                </h3>

                {/* Show graphs */}
                {results.correlation_graph && (
                  <img
                    src={`data:image/png;base64,${results.correlation_graph}`}
                    alt="Correlation Graph"
                    className="rounded-lg shadow"
                  />
                )}
                {results.spread_zscore_graph && (
                  <img
                    src={`data:image/png;base64,${results.spread_zscore_graph}`}
                    alt="Spread & Z-score"
                    className="rounded-lg shadow"
                  />
                )}
                {results.rolling_mean_graph && (
                  <img
                    src={`data:image/png;base64,${results.rolling_mean_graph}`}
                    alt="Rolling Mean"
                    className="rounded-lg shadow"
                  />
                )}

                {/* Trade signal */}
                {results.trade_signal && (
                  <div className="text-sm font-medium">
                    Signal: {results.trade_signal.buy} |{" "}
                    {results.trade_signal.sell}
                  </div>
                )}
              </div>
            ) : (
              <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
                <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">
                  Analysis Results
                </h3>
                <p className="text-muted-foreground">
                  {selectedStockA && selectedStockB
                    ? `Click "Run Analysis" to analyze ${selectedStockA} and ${selectedStockB}`
                    : "Select two stocks and run analysis to see results."}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
