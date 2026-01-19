import { Suspense } from "react";
import { useRoutes } from "react-router-dom";
//Navigate
import routes from "@/routes";

export default function App() {
  const router = useRoutes([
    ...routes,
    //{ path: "/admin", element: <Navigate to="/chat/admin" /> },
  ]);

  return <Suspense fallback={<p>Loading...</p>}>{router}</Suspense>;
}
