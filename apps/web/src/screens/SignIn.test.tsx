import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SignIn from "./SignIn";

describe("SignIn", () => {
  it("renders the Google sign-in link", () => {
    render(<SignIn />);
    expect(screen.getByText("Continue with Google")).toBeInTheDocument();
  });
});
