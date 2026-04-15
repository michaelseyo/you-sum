export type ExtensionUser = {
  email: string;
  name?: string;
  picture?: string;
  sub?: string;
};

export type AuthState = {
  accessToken: string;
  expiresAt: number;
  user: ExtensionUser;
};

export type VideoContext = {
  title: string;
  url: string;
  videoId: string | null;
};

export type SummarizeResponse = {
  summary: string;
};

export type SummarizeStreamEvent =
  | {
      message: string;
      type: "status";
    }
  | {
      text: string;
      type: "delta";
    }
  | {
      cached: boolean;
      prompt_version: string;
      type: "done";
    }
  | {
      message: string;
      type: "error";
    };

export type GoogleAuthExchangeResponse = {
  access_token: string;
  expires_at: number;
  user: ExtensionUser;
};

export type AuthGetStateMessage = {
  type: "AUTH_GET_STATE";
};

export type AuthSignInMessage = {
  type: "AUTH_SIGN_IN";
};

export type AuthSignOutMessage = {
  type: "AUTH_SIGN_OUT";
};

export type GetVideoContextMessage = {
  type: "GET_VIDEO_CONTEXT";
};

export type AuthRuntimeMessage =
  | AuthGetStateMessage
  | AuthSignInMessage
  | AuthSignOutMessage;

export type RuntimeMessage = AuthRuntimeMessage | GetVideoContextMessage;

export type AuthStateRuntimeResponse =
  | {
      authState: AuthState | null;
      ok: true;
    }
  | {
      error: string;
      ok: false;
    };

export type RuntimeMutationResponse =
  | {
      ok: true;
    }
  | {
      error: string;
      ok: false;
    };
