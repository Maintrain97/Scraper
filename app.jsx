import { useState } from "react";
import { Button, Input, Card, CardContent } from "@/components/ui";

export default function WebScraperUI() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleScrape = async () => {
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch("/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: "Failed to scrape data." });
    }

    setLoading(false);
  };

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-4">Web Scraper</h1>
      <Input 
        type="text" 
        placeholder="Enter URL" 
        value={url} 
        onChange={(e) => setUrl(e.target.value)} 
        className="mb-4 w-full" 
      />
      <Button onClick={handleScrape} disabled={loading} className="w-full">
        {loading ? "Scraping..." : "Scrape"}
      </Button>
      {result && (
        <Card className="mt-4">
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
