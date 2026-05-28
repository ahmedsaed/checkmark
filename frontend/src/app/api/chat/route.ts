// assistant-ui chat route — proxy to backend SSE stream
// The backend provides match agent messages via SSE; this route
// streams them as assistant-ui compatible chat events.

import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const { matchId } = await request.json();

  if (!matchId) {
    return NextResponse.json({ error: "matchId required" }, { status: 400 });
  }

  // Proxy to backend SSE endpoint
  const backendUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/matches/${matchId}/stream`;

  try {
    const response = await fetch(backendUrl);

    return new NextResponse(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 502 },
    );
  }
}
