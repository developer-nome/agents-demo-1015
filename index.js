#!/usr/bin/env node

import { FastMCP } from "fastmcp";
import { z } from "zod"; // Or any validation library that supports Standard Schema

const server = new FastMCP({
  name: "Flight Info Bot",
  version: "1.0.0",
});

server.addTool({
  name: "FlightInfoBot",
  description: "Returns flight information based on city.",
  parameters: z.object({
    a: z.string(),
  }),
  execute: async (args) => {
    switch (args.a) {
      case "Los Angeles":
        return "AA1234 Departing at 9:30 AM";
      case "Chicago": 
        return "DL2478 Departing at 10:00 AM";
      case "New York":
        return "UA5678 Departing at 11:15 AM";
      case "Miami":
        return "SW4321 Departing at 1:45 PM";
      case "San Francisco":
        return "BA8765 Departing at 2:30 PM";
      case "Seattle":
        return "AS3456 Departing at 3:00 PM";
      case "Boston":
        return "FR7890 Departing at 4:20 PM";
      case "Dallas":
        return "VX6543 Departing at 5:10 PM";
      default:
        return "No flight information available for the specified city.";
    }
  }
});

server.listRoots = async () => {
  return []; // empty list means: no roots supported
};

server.start({
  transportType: "stdio",
});
