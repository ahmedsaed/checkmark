export default function ModelDetail({ params }: { params: Promise<{ modelId: string }> }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-8">Model Detail</h1>
      <p className="text-zinc-400">Loading model...</p>
    </div>
  );
}
