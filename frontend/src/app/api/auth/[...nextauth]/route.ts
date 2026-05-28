import NextAuth from "next-auth";
import { auth } from "@/lib/auth";

// For next-auth v4, we need to use the handler directly
const handler = auth;

export { handler as GET, handler as POST };
