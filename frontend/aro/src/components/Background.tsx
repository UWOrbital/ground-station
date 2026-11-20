import background from "../assets/galaxy.jpg";

/**
 * @brief Background component displaying the Earth image
 * @return tsx element of Background component
 */
function Background() {
  return (
    <>
      <img
        src={background}
        alt="background-image"
        className="fixed inset-0 w-full h-full object-cover -z-20 blur-[0.4px] scale-105"
      />
      <div
        data-testid="background-overlay"
        className="fixed inset-0 -z-10 bg-gradient-to-b from-gray-950/80 via-gray-950/20 to-gray-950/80"
      />
    </>
  );
}

export default Background;
