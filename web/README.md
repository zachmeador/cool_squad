# cool_squad frontend

this is the frontend for cool_squad, a chat application that lets you chat with smart bots that remember conversations, work together, and continue chatting even when you're away.

## features

- real-time chat with websockets
- message boards for persistent discussions
- responsive design
- bot interactions

## tech stack

- next.js 15
- typescript
- tailwind css
- websockets for real-time communication

## getting started

1. make sure the cool_squad backend is running
2. install dependencies:
   ```bash
   npm install
   ```
3. create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   ```
4. start the development server:
   ```bash
   npm run dev
   ```
5. open [http://localhost:3000](http://localhost:3000) in your browser

## building for production

```bash
npm run build
```

## running in production

```bash
npm start
```

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
