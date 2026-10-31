import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_DERA_API_URL: z.string().url().default("http://localhost:8000"),
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
  NEXT_PUBLIC_ENABLE_SNAPSHOTS: z
    .string()
    .optional()
    .transform((val) => val === "true" || val === "1"),
  NEXT_PUBLIC_ENABLE_EXPORTS: z
    .string()
    .optional()
    .transform((val) => val === "true" || val === "1"),
});

export type ClientEnv = z.infer<typeof envSchema>;

export function getClientEnv(): ClientEnv {
  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_DERA_API_URL: process.env.NEXT_PUBLIC_DERA_API_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_ENABLE_SNAPSHOTS: process.env.NEXT_PUBLIC_ENABLE_SNAPSHOTS,
    NEXT_PUBLIC_ENABLE_EXPORTS: process.env.NEXT_PUBLIC_ENABLE_EXPORTS,
  });

  if (!parsed.success) {
    console.error("Invalid frontend environment variables:", parsed.error.format());
    return {
      NEXT_PUBLIC_DERA_API_URL: "http://localhost:8000",
      NEXT_PUBLIC_APP_URL: "http://localhost:3000",
      NEXT_PUBLIC_ENABLE_SNAPSHOTS: true,
      NEXT_PUBLIC_ENABLE_EXPORTS: true,
    };
  }

  return parsed.data;
}

export const env = getClientEnv();
