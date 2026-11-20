import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useCreatePictureRequest, usePictureRequests } from "./usePictureRequests";
import { API_BASE_URL, ApiError } from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import { createQueryWrapper, jsonResponse } from "./testUtils";

/**
 * @brief Build a picture request as the backend serializes it.
 * @param overrides fields to replace on the default request.
 * @return a PictureRequestItem-shaped body.
 */
function pictureRequest(overrides: Record<string, unknown> = {}) {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    aro_id: "22222222-2222-2222-2222-222222222222",
    // Backend Decimals serialize as JSON strings.
    latitude: "43.470",
    longitude: "-80.540",
    created_on: "2026-01-01T00:00:00Z",
    request_sent_to_obc_on: null,
    pic_taken_on: null,
    pic_transmitted_on: null,
    delete_deadline: "2026-01-02T00:00:00Z",
    packet_id: null,
    status: "pending",
    operations: {},
    ...overrides,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
  accessTokenStore.set("abc");
});

describe("usePictureRequests", () => {
  it("returns the unwrapped request list and encodes paging in the query string", async () => {
    const requests = [pictureRequest()];
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: requests, operations: {} }),
    } as Response);

    const { result } = renderHook(() => usePictureRequests(50, 10), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(requests);

    const calledUrl = String(fetchSpy.mock.calls[0][0]);
    expect(calledUrl).toContain("/requests/?");
    expect(calledUrl).toContain("limit=50");
    expect(calledUrl).not.toContain("count=");
    expect(calledUrl).toContain("offset=10");
    const headers = (fetchSpy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer abc");
  });

  it("throws an ApiError on a failed response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "boom" }),
    } as Response);

    const { result } = renderHook(() => usePictureRequests(), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(500);
  });
});

describe("useCreatePictureRequest", () => {
  it("posts the coordinates with the bearer token and returns the created request", async () => {
    const created = pictureRequest({ latitude: "43.472", longitude: "-80.545" });
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(200, { data: created }));

    const { result } = renderHook(() => useCreatePictureRequest(), {
      wrapper: createQueryWrapper(),
    });

    let returned: unknown;
    await act(async () => {
      returned = await result.current.mutateAsync({ latitude: 43.472, longitude: -80.545 });
    });

    expect(returned).toEqual(created);
    expect(fetchSpy).toHaveBeenCalledOnce();
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/requests/`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ latitude: 43.472, longitude: -80.545 });
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer abc");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("refetches picture-request lists after a successful create", async () => {
    let listCalls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method === "POST") return jsonResponse(200, { data: pictureRequest() });
      listCalls += 1;
      return jsonResponse(200, { data: [], operations: {} });
    });

    const { result } = renderHook(
      () => ({ list: usePictureRequests(), create: useCreatePictureRequest() }),
      { wrapper: createQueryWrapper() },
    );
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true));
    expect(listCalls).toBe(1);

    await act(async () => {
      await result.current.create.mutateAsync({ latitude: 1, longitude: 2 });
    });

    await waitFor(() => expect(listCalls).toBe(2));
  });

  it("throws an ApiError when the backend rejects the request", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(422));

    const { result } = renderHook(() => useCreatePictureRequest(), {
      wrapper: createQueryWrapper(),
    });
    act(() => result.current.mutate({ latitude: 0, longitude: 0 }));

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(422);
  });
});
