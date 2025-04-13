"use client"

import { useState } from "react"
import { Search, Download, ChevronDown, Check, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import Image from "next/image"

// Types based on the backend API
interface SpotifyInfo {
  title: string
  artists: string
  id: string
}

interface YoutubeInfo {
  thumbnail: string | null
  title: string | null
  channel: string | null
  duration: string | null
  views: number | null
  url: string | null
}

interface TrackInfo {
  spotify: SpotifyInfo
  youtube: YoutubeInfo[]
}

interface SearchResponse {
  playlist_name: string
  tracks: TrackInfo[]
}

interface DownloadTrack {
  spotify_id: string
  url: string
}

export default function Home() {
  const [playlistUrl, setPlaylistUrl] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [searchError, setSearchError] = useState("")
  const [playlistData, setPlaylistData] = useState<SearchResponse | null>(null)
  const [selectedVideos, setSelectedVideos] = useState<Record<string, number>>({})

  // Validate Spotify URL with regex
  const isValidSpotifyUrl = (url: string) => {
    const pattern = /https?:\/\/open\.spotify\.com\/playlist\/[\w\d]+/
    return pattern.test(url)
  }

  // Handle search button click
  const handleSearch = async () => {
    if (!isValidSpotifyUrl(playlistUrl)) {
      setSearchError("URL inválida. Por favor, insira uma URL válida do Spotify.")
      return
    }

    setSearchError("")
    setIsSearching(true)

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: playlistUrl }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Erro ao buscar playlist")
      }

      const data: SearchResponse = await response.json()

      // Initialize selected videos to the first option (index 0) for each track
      const initialSelections: Record<string, number> = {}
      data.tracks.forEach((track) => {
        initialSelections[track.spotify.id] = 0
      })

      setSelectedVideos(initialSelections)
      setPlaylistData(data)
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Erro desconhecido")
    } finally {
      setIsSearching(false)
    }
  }

  // Handle download button click
  const handleDownload = async () => {
    if (!playlistData) return

    setIsDownloading(true)

    try {
      const tracks: DownloadTrack[] = playlistData.tracks.map((track) => ({
        spotify_id: track.spotify.id,
        url: track.youtube[selectedVideos[track.spotify.id]].url || "",
      }))

      const response = await fetch("/api/download", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          playlist_name: playlistData.playlist_name,
          tracks,
        }),
      })

      if (!response.ok) {
        throw new Error("Erro ao baixar playlist")
      }

      // Create a blob from the response and trigger download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${playlistData.playlist_name}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      a.remove()
    } catch (error) {
      console.error("Download error:", error)
      alert("Erro ao baixar a playlist. Por favor, tente novamente.")
    } finally {
      setIsDownloading(false)
    }
  }

  // Handle video selection change
  const handleVideoChange = (trackId: string, videoIndex: number) => {
    setSelectedVideos((prev) => ({
      ...prev,
      [trackId]: videoIndex,
    }))
  }

  // Format view count
  const formatViews = (views: number | null) => {
    if (views === null) return "N/A"

    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`
    } else if (views >= 1000) {
      return `${(views / 1000).toFixed(1)}K`
    }
    return views.toString()
  }

  return (
    <main className="container mx-auto p-4 max-w-6xl">
      <div className={`transition-all duration-300 ${playlistData ? "py-4" : "py-20"}`}>
        <h1
          className={`text-center font-bold transition-all duration-300 ${playlistData ? "text-2xl mb-4" : "text-4xl mb-8"}`}
        >
          Spotify Playlist Downloader
        </h1>

        <div className="flex gap-2 max-w-2xl mx-auto">
          <Input
            type="text"
            placeholder="Cole a URL da playlist do Spotify"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            className="flex-1"
          />
          <Button onClick={handleSearch} disabled={isSearching}>
            {isSearching ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
            Pesquisar
          </Button>
        </div>

        {searchError && <p className="text-red-500 text-center mt-2">{searchError}</p>}
      </div>

      {playlistData && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-4">Playlist: {playlistData.playlist_name}</h2>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-muted">
                  <th className="p-2 text-left">Thumbnail</th>
                  <th className="p-2 text-left">Título</th>
                  <th className="p-2 text-left">Canal</th>
                  <th className="p-2 text-left">Duração</th>
                  <th className="p-2 text-left">Views</th>
                  <th className="p-2 text-left">Opções</th>
                </tr>
              </thead>
              <tbody>
                {playlistData.tracks.map((track) => {
                  const selectedIndex = selectedVideos[track.spotify.id]
                  const selectedVideo = track.youtube[selectedIndex]

                  return (
                    <tr key={track.spotify.id} className="border-b hover:bg-muted/50">
                      <td className="p-2">
                        {selectedVideo.thumbnail ? (
                          <Image
                            src={selectedVideo.thumbnail || "/placeholder.svg"}
                            alt={selectedVideo.title || ""}
                            width={120}
                            height={68}
                            className="rounded object-cover"
                          />
                        ) : (
                          <div className="w-[120px] h-[68px] bg-muted rounded flex items-center justify-center">
                            No thumbnail
                          </div>
                        )}
                      </td>
                      <td className="p-2">
                        <div className="font-medium">{selectedVideo.title || "N/A"}</div>
                        <div className="text-sm text-muted-foreground">
                          {track.spotify.title} - {track.spotify.artists}
                        </div>
                      </td>
                      <td className="p-2">{selectedVideo.channel || "N/A"}</td>
                      <td className="p-2">{selectedVideo.duration || "N/A"}</td>
                      <td className="p-2">{formatViews(selectedVideo.views)}</td>
                      <td className="p-2">
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button variant="outline" size="sm">
                              Change <ChevronDown className="ml-2 h-4 w-4" />
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-[350px] p-0" align="end">
                            <div className="space-y-2 p-2">
                              {track.youtube.map((video, index) => (
                                <div
                                  key={index}
                                  className={`flex items-start gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                                    selectedIndex === index ? "bg-muted" : ""
                                  }`}
                                  onClick={() => handleVideoChange(track.spotify.id, index)}
                                >
                                  {video.thumbnail ? (
                                    <Image
                                      src={video.thumbnail || "/placeholder.svg"}
                                      alt={video.title || ""}
                                      width={80}
                                      height={45}
                                      className="rounded object-cover"
                                    />
                                  ) : (
                                    <div className="w-[80px] h-[45px] bg-muted rounded flex items-center justify-center">
                                      No thumbnail
                                    </div>
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate">{video.title || "N/A"}</div>
                                    <div className="text-xs text-muted-foreground">{video.duration || "N/A"}</div>
                                  </div>
                                  {selectedIndex === index && <Check className="h-4 w-4 text-primary" />}
                                </div>
                              ))}
                            </div>
                          </PopoverContent>
                        </Popover>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex justify-center">
            <Button onClick={handleDownload} disabled={isDownloading} size="lg">
              {isDownloading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processando...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Baixar Playlist em ZIP
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </main>
  )
}
