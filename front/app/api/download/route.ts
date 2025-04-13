import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Encaminha a requisição para o backend FastAPI
    const backendResponse = await fetch("http://localhost:8000/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    console.log('aqui 0')

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      return NextResponse.json(
        { detail: errorData.detail || "Erro ao baixar playlist" },
        { status: backendResponse.status }
      );
    }

    console.log('aqui 1')
    // Lê a resposta do FastAPI como ArrayBuffer
    const arrayBuffer = await backendResponse.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    console.log('aqui 2')
    // Cria um nome de arquivo seguro (codifica caracteres especiais)
    const fileName = `${body.playlist_name}.zip`;
    const encodedFileName = encodeURIComponent(fileName);
    
    // Retorna a resposta com os cabeçalhos adequados
    console.log('aqui 3')
    return new NextResponse(buffer, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename*=UTF-8''${encodedFileName}`,
      },
    });

  } catch (error) {
    console.error("Download API error:", error);
    return NextResponse.json(
      { detail: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}
