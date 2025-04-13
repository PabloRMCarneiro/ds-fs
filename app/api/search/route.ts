import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { url } = body

    // Forward the request to your FastAPI backend
    const response = await fetch("http://localhost:8000/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ detail: errorData.detail || "Erro ao buscar playlist" }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Search API error:", error)
    return NextResponse.json({ detail: "Erro interno do servidor" }, { status: 500 })
  }
}
