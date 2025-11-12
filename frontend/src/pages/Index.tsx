import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Zap } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-6">
              Twin Trade
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
              Twin Trade empowers you to analyze stock pairs, uncover hidden relationships, and
              trade with precision powered by data-driven insights.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/signup">
                <Button variant="gradient" size="lg" className="w-full sm:w-auto">
                  Create Account
                </Button>
              </Link>
              <Link to="/signin">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Powerful Trading Features</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to succeed in pairs trading, from market analysis to automated execution
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Automatic Mode Card */}
            <Link to="/automatic-mode">
              <Card className="shadow-card hover:shadow-elegant transition-smooth text-center cursor-pointer">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-primary rounded-lg mx-auto mb-4 flex items-center justify-center">
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">Automatic Mode</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm">
                    Detect top-performing stock pairs automatically.
                  </p>
                </CardContent>
              </Card>
            </Link>

            {/* Custom Analysis Card */}
            <Link to="/custom-mode">
              <Card className="shadow-card hover:shadow-elegant transition-smooth text-center cursor-pointer">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-accent rounded-lg mx-auto mb-4 flex items-center justify-center">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">Custom Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm">
                    Explore pair relationships with detailed analysis tools.
                  </p>
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Start Pair Trading?
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            Join thousands of traders using statistical arbitrage to generate consistent returns
          </p>
          <Link to="/signup">
            <Button variant="gradient" size="lg">
              Create Your Account
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Index;
