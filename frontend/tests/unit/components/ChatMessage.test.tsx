/**
 * @file Unit tests for the ChatMessage component.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ChatMessage } from "@/components/chat/ChatMessage";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

const makeMessage = (role: ChatMessageType["role"], content: string): ChatMessageType => ({
  id: "test-id",
  role,
  content,
  timestamp: new Date("2024-01-01T00:00:00Z"),
});

describe("ChatMessage", () => {
  it("renders user message content", () => {
    render(<ChatMessage message={makeMessage("user", "Hello cluster!")} />);
    expect(screen.getByText("Hello cluster!")).toBeInTheDocument();
  });

  it("renders assistant message content", () => {
    render(<ChatMessage message={makeMessage("assistant", "Here are your pods.")} />);
    expect(screen.getByText("Here are your pods.")).toBeInTheDocument();
  });

  it("renders system message as centered notice", () => {
    const { container } = render(<ChatMessage message={makeMessage("system", "Command cancelled.")} />);
    expect(screen.getByText("Command cancelled.")).toBeInTheDocument();
    // System messages are centered.
    expect(container.querySelector(".justify-center")).toBeInTheDocument();
  });

  it("assistant message has purple left border", () => {
    const { container } = render(<ChatMessage message={makeMessage("assistant", "Response")} />);
    const bubble = container.querySelector(".border-kn-purple");
    expect(bubble).toBeInTheDocument();
  });

  it("user message does not have purple border", () => {
    const { container } = render(<ChatMessage message={makeMessage("user", "Question")} />);
    expect(container.querySelector(".border-kn-purple")).not.toBeInTheDocument();
  });
});
