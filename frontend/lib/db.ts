import { neon } from '@neondatabase/serverless';

if (!process.env.DATABASE_URL) {
  throw new Error(
    'DATABASE_URL is not set. Add it to .env.local for Server Component reads.'
  );
}

const sql = neon(process.env.DATABASE_URL);

export { sql };
