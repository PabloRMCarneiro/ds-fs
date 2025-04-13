import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()

    // Forward the request to your FastAPI backend
    const response = await fetch("http://localhost:8000/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json({ detail: "Erro ao baixar playlist" }, { status: response.status })
    }

    // Get the ZIP file from the backend
    const zipData = await response.arrayBuffer()

    // Return the ZIP file to the client
    return new NextResponse(zipData, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${body.playlist_name}.zip"`,
      },
    })
  } catch (error) {
    console.error("Download API error:", error)
    return NextResponse.json({ detail: "Erro interno do servidor" }, { status: 500 })
  }
}
