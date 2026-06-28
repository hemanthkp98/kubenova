/**
 * @file Unit tests for the useWebSocket hook.
 *
 * Uses a mock WebSocket implementation to test reconnect and queuing behaviour.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "@/hooks/useWebSocket";

// ---- Mock WebSocket ----
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  static CONNECTING = 0;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  onopen: ((e: Event) => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  onclose: ((e: CloseEvent) => void) | null = null;
  sent: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => this.onopen?.(new Event("open")), 0);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close(code = 1000) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code } as CloseEvent);
  }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllTimers();
});

describe("useWebSocket", () => {
  it("connects to the given URL", async () => {
    renderHook(() => useWebSocket("ws://test/chat"));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toBe("ws://test/chat");
  });

  it("reports isConnected=true after open event", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test/chat"));
    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });
    expect(result.current.isConnected).toBe(true);
  });

  it("calls onMessage callback when a message arrives", async () => {
    const onMessage = vi.fn();
    renderHook(() => useWebSocket("ws://test/chat", { onMessage }));
    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
      MockWebSocket.instances[0].onmessage?.({ data: "hello" } as MessageEvent);
    });
    expect(onMessage).toHaveBeenCalledWith("hello");
  });

  it("queues messages when disconnected and flushes on reconnect", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test/chat"));
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    // Disconnect.
    act(() => { MockWebSocket.instances[0].close(1006); });
    expect(result.current.isConnected).toBe(false);

    // Queue a message.
    act(() => { result.current.sendMessage("queued-message"); });

    // Wait for reconnect.
    await act(async () => { await new Promise((r) => setTimeout(r, 1100)); });

    const latestWS = MockWebSocket.instances[MockWebSocket.instances.length - 1];
    expect(latestWS.sent).toContain("queued-message");
  });

  it("sends message immediately when connected", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test/chat"));
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
    act(() => { result.current.sendMessage("direct-message"); });
    expect(MockWebSocket.instances[0].sent).toContain("direct-message");
  });

  it("reports isConnected=false after close", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test/chat"));
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
    act(() => { MockWebSocket.instances[0].close(1000); });
    expect(result.current.isConnected).toBe(false);
  });
});
