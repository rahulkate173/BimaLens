import { create } from 'zustand';

const useStore = create((set, get) => ({
  // ── Policies ────────────────────────────────────────────────
  policies: [],
  setPolicies: (policies) => set({ policies }),
  addPolicy: (policy) => set((s) => ({ policies: [policy, ...s.policies] })),

  // ── Selected policy ─────────────────────────────────────────
  selectedPolicy: null,
  setSelectedPolicy: (policy) => set({ selectedPolicy: policy }),

  // ── Analysis data ───────────────────────────────────────────
  analysisData: null,
  setAnalysisData: (data) => set({ analysisData: data }),

  // ── Chat messages per policy ────────────────────────────────
  chatMessages: [],
  setChatMessages: (msgs) => set({ chatMessages: msgs }),
  addChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),

  // ── Upload status ───────────────────────────────────────────
  uploadStatus: { uploading: false, progress: 0, processing: false, error: null },
  setUploadStatus: (patch) =>
    set((s) => ({ uploadStatus: { ...s.uploadStatus, ...patch } })),
  resetUploadStatus: () =>
    set({ uploadStatus: { uploading: false, progress: 0, processing: false, error: null } }),

  // ── Loading states ──────────────────────────────────────────
  loading: { policies: false, analysis: false, ask: false },
  setLoading: (key, value) =>
    set((s) => ({ loading: { ...s.loading, [key]: value } })),
}));

export default useStore;
