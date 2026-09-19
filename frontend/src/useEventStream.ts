import { useEffect, useState } from "react";
import { connectEventStream } from "./api";
import type { StreamEvent } from "./types";

export function useEventStream(onEvent: (event: StreamEvent) => void) {
  const [connected, setConnected] = useState(false);

  useEffect(() => connectEventStream(onEvent, setConnected), [onEvent]);

  return connected;
}
