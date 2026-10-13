// import type { NextConfig } from "next";

// const nextConfig: NextConfig = {
//   output: "standalone",
//   async rewrites() {
//     return [
//       {
//         source: "/api/:path*",
//         destination: "https://salep-staging.icdigital.io/api/:path*",
//       },
//     ];
//   },
// };

// export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
