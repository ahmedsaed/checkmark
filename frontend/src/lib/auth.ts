import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const auth = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const adminUser = process.env.ADMIN_USERNAME;
        const adminPass = process.env.ADMIN_PASSWORD;

        if (
          !adminUser ||
          !adminPass ||
          credentials?.username === adminUser &&
          credentials?.password === adminPass
        ) {
          return { id: "1", name: adminUser, role: "admin" };
        }

        return null;
      },
    }),
  ],
  pages: {
    signIn: "/admin/login",
  },
  session: { strategy: "jwt" },
  callbacks: {
    jwt({ token, user }) {
      if (user) (token as any).role = (user as any).role;
      return token;
    },
    session({ session, token }) {
      (session as any).user.role = token.role as string;
      return session;
    },
  },
});

export const { GET, POST } = auth;
