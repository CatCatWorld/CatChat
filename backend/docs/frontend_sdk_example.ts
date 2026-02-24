import axios, { AxiosInstance } from "axios";

export type ViewMode = "god" | `player:${string}`;

export interface RoomConfig {
  room_id: string;
  player_count: number;
  role_distribution: Record<string, number>;
  night_order: string[];
  warnings: string[];
}

export interface WsMessage<T = unknown> {
  event_id?: number;
  event: string;
  payload: T;
  ts?: string;
}

export class WerewolfApiClient {
  private readonly http: AxiosInstance;

  constructor(baseURL: string) {
    this.http = axios.create({ baseURL });
  }

  async createRoom(playerCount: number, ownerNickname = "admin") {
    const { data } = await this.http.post("/api/rooms", {
      owner_nickname: ownerNickname,
      player_count: playerCount,
    });
    return data;
  }

  async createAiRoom(playerCount: number, ownerNickname = "cat_01") {
    const { data } = await this.http.post("/api/ai/rooms", {
      owner_nickname: ownerNickname,
      player_count: playerCount,
    });
    return data;
  }

  async getRoomConfig(roomId: string): Promise<RoomConfig> {
    const { data } = await this.http.get(`/api/rooms/${roomId}/config`);
    return data;
  }

  async registerAgent(params: {
    room_id: string;
    player_id: string;
    endpoint: string;
    model: string;
    timeout_sec?: number;
    api_url?: string;
    api_key?: string;
    model_name?: string;
    cli_command?: string;
    cli_timeout_sec?: number;
  }) {
    const { data } = await this.http.post("/api/agents/register", params);
    return data;
  }

  async getAgentsStatus(roomId: string) {
    const { data } = await this.http.get("/api/agents/status", {
      params: { room_id: roomId },
    });
    return data;
  }
}

export class WerewolfWsClient {
  private ws?: WebSocket;

  connect(url: string, roomId: string, viewMode: ViewMode, onEvent: (msg: WsMessage) => void) {
    this.ws = new WebSocket(url);
    this.ws.onopen = () => {
      this.ws?.send(
        JSON.stringify({
          type: "subscribe",
          room_id: roomId,
          view_mode: viewMode,
        }),
      );
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data) as WsMessage;
      onEvent(msg);
    };
  }

  switchView(mode: ViewMode) {
    this.ws?.send(JSON.stringify({ type: "change_view", mode }));
  }

  sendAction(event: string, payload: Record<string, unknown>) {
    this.ws?.send(JSON.stringify({ event, payload }));
  }

  close() {
    this.ws?.close();
  }
}
