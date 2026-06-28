/**
 * @file Unit tests for the ChatInput component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ChatInput } from "@/components/chat/ChatInput";

describe("ChatInput", () => {
  it("renders the textarea and send button", () => {
    render(<ChatInput onSend={vi.fn()} />);
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
    expect(screen.getByTestId("send-button")).toBeInTheDocument();
  });

  it("calls onSend when Enter is pressed", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const input = screen.getByTestId("chat-input");
    await user.type(input, "show pods{Enter}");
    expect(onSend).toHaveBeenCalledWith("show pods");
  });

  it("inserts newline on Shift+Enter without sending", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const input = screen.getByTestId("chat-input");
    await user.type(input, "line1{Shift>}{Enter}{/Shift}line2");
    expect(onSend).not.toHaveBeenCalled();
    expect((input as HTMLTextAreaElement).value).toContain("line1");
  });

  it("does not call onSend for empty input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const button = screen.getByTestId("send-button");
    await user.click(button);
    expect(onSend).not.toHaveBeenCalled();
  });

  it("clears input after successful send", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} />);
    const input = screen.getByTestId("chat-input") as HTMLTextAreaElement;
    await user.type(input, "test message");
    await user.keyboard("{Enter}");
    expect(input.value).toBe("");
  });

  it("send button is disabled when input is empty", () => {
    render(<ChatInput onSend={vi.fn()} />);
    expect(screen.getByTestId("send-button")).toBeDisabled();
  });
});
