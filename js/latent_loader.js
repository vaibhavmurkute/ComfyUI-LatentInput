import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
	name: "Comfy.LatentLoader.Advanced.Final", // Use new name to avoid browser cache issues
	async beforeRegisterNodeDef(nodeType, nodeData) {
		if (nodeData.name === "LatentLoaderAdvanced") {
			
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				onNodeCreated?.apply(this, arguments);

				// Shared function for uploading files
				const uploadFile = async (file) => {
					try {
						const body = new FormData();
						// Upload file to temp directory to avoid overwrite issues
						body.append("image", file);
						body.append("overwrite", "true");
						body.append("type", "temp"); // Add this line
						const resp = await api.fetchApi("/upload/image", {
							method: "POST",
							body,
						});

						if (resp.status === 200) {
							const data = await resp.json();
							// Ensure path includes subfolder and type
							const path = `${data.type}/${data.subfolder ? `${data.subfolder}/` : ''}${data.name}`;
							const textWidget = this.widgets.find((w) => w.name === "latent_file");
							if (textWidget) {
								textWidget.value = path;
							}
						} else {
							alert(`Upload Error: ${resp.status} - ${resp.statusText}`);
						}
					} catch (error) {
						console.error("Upload failed:", error);
						alert(`Upload failed: ${error}`);
					}
				};

				// Upload button logic
				this.addWidget("button", "upload_latent", "Upload Latent", () => {
					const inputEl = document.createElement("input");
					inputEl.type = "file";
					inputEl.accept = ".latent";
					document.body.appendChild(inputEl);
					
					const handleFileSelect = () => {
						if (inputEl.files.length > 0) {
							uploadFile(inputEl.files[0]);
						}
						inputEl.remove();
					};

					inputEl.addEventListener("change", handleFileSelect);
					inputEl.style.display = "none";
					inputEl.click();
				});

				// Drag and drop event handling
				this.onDragOver = function(e) {
					// Check if dragged items are files
					if (e.dataTransfer?.types.includes("Files")) {
						e.preventDefault(); // Key: prevent browser default behavior to allow drop
						return true;
					}
					return false;
				};
	
				this.onDragDrop = async function(e) {
					e.preventDefault();  // Key: prevent browser default behavior
					e.stopPropagation(); // Optional: prevent event bubbling
					
					let handled = false;
					for (const file of e.dataTransfer.files) {
						if (file.name.endsWith(".latent")) {
							await uploadFile(file); // Wait for upload completion
							handled = true;
							break; // Only process the first valid file
						}
					}
					return handled;
				};
			};
		}
	},
});