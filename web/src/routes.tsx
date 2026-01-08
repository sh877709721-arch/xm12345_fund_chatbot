import { lazy } from "react";

// Layouts
import { DashboardLayout } from "@/components/admin/dashboard-layout";
//import { BotLayout } from "@/components/admin/bot-layout";
import { ProtectedRoute } from "@/components/auth/protected-route";

// Pages
const DashboardMain = lazy(() => import("@/pages/admin/main"));
const Analytics = lazy(() => import("@/pages/admin/analytics"));
const Team = lazy(() => import("@/pages/admin/team"));
const Settings = lazy(() => import("@/pages/admin/settings"));
const About = lazy(() => import("@/pages/about"));
const Home = lazy(() => import("@/pages/index"));
const NotFound = lazy(() => import("@/pages/404"));

//login and register
const LoginPage = lazy(() => import("@/pages/login"));
//const RegisterPage = lazy(() => import("@/pages/register"));

// Auth redirect component
import { AuthRedirect } from "@/components/auth/auth-redirect";

//知识库管理界面
const KnowledgeList = lazy(
  () => import("@/pages/admin/knowledge/knowledge-list-page")
);
const KnowledgeLabeling = lazy(
  () => import("@/pages/admin/knowledge/knowledge-search")
);
const KnowledgeSearch = lazy(
  () => import("@/pages/admin/knowledge/knowledge-search")
);

//后台管理界面
const TestingBotPage = lazy(() => import("@/pages/admin/bot/testing"));
const VoteMessages = lazy(() => import("@/pages/admin/bot/vote-messages"));
//const InstructionPage = lazy(() => import("@/pages/admin/bot/instruction"));
const FeedbackPage = lazy(() => import("@/pages/admin/bot/feedback"));

//Guideline 管理界面
const GuidelineList = lazy(() => import("@/pages/admin/guideline/guideline-list-page"));
const GuidelineMatchTest = lazy(() => import("@/pages/admin/guideline/guideline-match-test"));
const BotChat = lazy(() => import("@/pages/admin/bot/bot-chat"));

//主界面
import { AppLayout } from "@/components/app/app-layout";
import { ChatProviderWrapper } from "@/components/admin/chat-provider-wrapper";

const routes = [
  { path: "/about", element: <About /> },
  {
    path: "/login",
    element: (
      <AuthRedirect>
        <LoginPage />
      </AuthRedirect>
    )
  },
  // { path: "/register", element: <RegisterPage /> },
  {
    path: "/",
    element: <AppLayout />,
    children: [{ index: true, element: <Home /> }],
  },
  {
    path: "/admin",
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardMain /> },
      { path: "knowledge-list", element: <KnowledgeList /> },
      {
        path: "knowledge-labeling",
        element: <KnowledgeLabeling />,
      },
      {
        path: "knowledge-search",
        element: <KnowledgeSearch />,
      },
      {
        path: "vote-messages",
        element: <VoteMessages />,
      },
      {
        path: "feedback",
        element: <FeedbackPage />,
      },
      {
        path: "bot-testing",
        element: <TestingBotPage />,
      },
      {
        path: "bot-instruction",
        element: <GuidelineList />
      },
      {
        path: "guideline-match-test",
        element: <GuidelineMatchTest />
      },
      {
        path: "bot-chat",
        element: <ChatProviderWrapper />,
        children: [
          {
            index: true,
            element: <BotChat />
          }
        ]
      },
      { path: "team", element: <Team /> },
      { path: "analytics", element: <Analytics /> },
      { path: "settings", element: <Settings /> },
      { path: "about", element: <About /> },
    ],
  },
  { path: "*", element: <NotFound /> },
];

export default routes;
