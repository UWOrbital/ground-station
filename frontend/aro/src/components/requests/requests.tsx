import {
  useDeletePictureRequest,
  usePictureRequests,
  type PictureRequest,
} from "@/hooks/usePictureRequests";
import { ApiError } from "@/lib/apiClient";
import toastService from "@/services/Toast.service";

/**
 * @brief Format an ISO timestamp for display in the user's locale.
 * @param iso the ISO datetime string from the backend.
 * @return the localized date and time.
 */
function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

/**
 * @brief Page listing the signed-in ARO user's picture requests.
 *
 * Actions are shown only when the backend includes them in a request's
 * `operations`, so the page never decides on its own whether one is allowed.
 *
 * @return tsx element of Requests page
 */
function Requests() {
  const { data: requests, isPending, isError } = usePictureRequests();
  const deleteRequest = useDeletePictureRequest();

  /**
   * @brief Ask for confirmation, then delete a request through its advertised URL.
   * @param url the request's `operations.delete.url`.
   */
  function handleDelete(url: string) {
    if (!window.confirm("Delete this picture request? This can't be undone.")) return;
    deleteRequest.mutate(url, {
      onSuccess: () => toastService.success("Picture request deleted."),
      onError: (error) =>
        toastService.error(
          error instanceof ApiError ? error.message : "Unable to delete the picture request.",
        ),
    });
  }

  /**
   * @brief Render the action buttons the backend allows for a request.
   * @param request the picture request to render actions for.
   * @return the action buttons, or a dash when none are available.
   */
  function renderActions(request: PictureRequest) {
    const deleteOperation = request.operations.delete;
    if (!deleteOperation) return <span className="text-gray-400">—</span>;

    const isDeleting = deleteRequest.isPending && deleteRequest.variables === deleteOperation.url;
    return (
      <div className="flex flex-col items-start gap-1">
        <button
          type="button"
          onClick={() => handleDelete(deleteOperation.url)}
          disabled={deleteRequest.isPending}
          className="border border-red-600 text-red-600 px-3 py-1 rounded-lg hover:bg-red-50 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isDeleting ? "Deleting…" : "Delete"}
        </button>
        {deleteOperation.deletable_until && (
          <span className="text-xs text-gray-500">
            until {formatDate(deleteOperation.deletable_until)}
          </span>
        )}
      </div>
    );
  }

  let content;
  if (isPending) {
    content = <p className="text-center text-gray-500">Loading your requests…</p>;
  } else if (isError) {
    content = (
      <p role="alert" className="text-center text-red-600">
        Unable to load your requests. Please try again.
      </p>
    );
  } else if (requests.length === 0) {
    content = <p className="text-center text-gray-500">You haven&apos;t made any requests yet.</p>;
  } else {
    content = (
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-300 text-gray-500">
              <th className="px-4 py-3 font-normal">Created</th>
              <th className="px-4 py-3 font-normal">Latitude</th>
              <th className="px-4 py-3 font-normal">Longitude</th>
              <th className="px-4 py-3 font-normal">Status</th>
              <th className="px-4 py-3 font-normal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id} className="border-b border-gray-200">
                <td className="px-4 py-3">{formatDate(request.created_on)}</td>
                <td className="px-4 py-3">{request.latitude}</td>
                <td className="px-4 py-3">{request.longitude}</td>
                <td className="px-4 py-3 capitalize">{request.status}</td>
                <td className="px-4 py-3">{renderActions(request)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center min-h-screen px-4 pt-32 pb-24">
      <div className="w-full max-w-5xl bg-white text-black rounded-lg p-6">
        <h1 className="text-2xl font-medium text-center mb-6">My requests</h1>
        {content}
      </div>
    </div>
  );
}

export default Requests;
