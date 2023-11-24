import React, { useState } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import Typography from "@mui/material/Typography";
import "@fontsource/league-spartan";

export function ApplyButton({ postingID, companyName }) {
  const [open, setOpen] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [coverLetterFile, setCoverLetterFile] = useState(null);
  const [submissionStatus, setSubmissionStatus] = useState("pending"); // 'pending', 'success'
  const [resumeUploadDate, setResumeUploadDate] = useState(null);
  const [coverLetterUploadDate, setCoverLetterUploadDate] = useState(null);
  const [displayResume, setDisplayResume] = useState(false);
  const [displayCoverLetter, setDisplayCoverLetter] = useState(false);
  const [applicationId, setApplicationId] = useState(null);

  const handleFileChange = (event, fileType) => {
    const fileInput = event.target;
    const currentDate = new Date(); // Get the current date and time
    const formattedDate = currentDate.toLocaleString(); // Format the date as a string
    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      // Set the corresponding file state based on the fileType
      if (fileType === "resume") {
        setResumeFile(file);
        setResumeUploadDate(formattedDate);
      } else {
        setCoverLetterFile(file);
        setCoverLetterUploadDate(formattedDate);
      }
    } else {
      // If no files are selected, reset the corresponding file state
      if (fileType === "resume") {
        setResumeFile(null);
        setResumeUploadDate(null);
      } else {
        setCoverLetterFile(null);
        setCoverLetterUploadDate(null);
      }
    }
  };

  const handleUploadButtonClick = (fileType) => {
    const fileInput = document.getElementById(`${fileType}Input`);
    if (fileInput) {
      fileInput.click();
    }
  };

  const handleSubmission = async () => {
    // Check if both resume and cover letter files are uploaded
    if (resumeFile && coverLetterFile) {
      const formData = new FormData();
      formData.append('resume', resumeFile);
      formData.append('coverLetter', coverLetterFile);
      formData.append('postingId', postingID);

      try 
      {
        const response = await fetch('/upload-pdf', {
          method: 'POST',
          body: formData,
        });

        // Update the submission status to indicate success
        if (response.ok)
        {
          const responseData = await response.json();
          setSubmissionStatus('success');
          setApplicationId(responseData.applicationId);
          console.log('Submission successful. Application ID:', responseData.applicationId);
        }
        else
        {
          console.error('Submission failed:', response.status);
        }
      } 

      catch (error) 
      {
        console.error('Error during submission:', error);
      }

      // Update the submission status to indicate success
      setSubmissionStatus("success");
      console.log("Submission successful");
    } else {
      // Display an error or prompt the user to upload both files
      console.error("Please upload both resume and cover letter files.");
    }
  };

  // WIP function to display the submitted pdf
  const handleDisplayResume = async () => {
    if (applicationId) {
      try {
        const response = await fetch(`/get-resume/${applicationId}`);
        if (response.ok) {
          // Get the blob data from the response
          const fileBlob = await response.blob();
          const fileURL = URL.createObjectURL(fileBlob);
  
          // Open the file URL in a new tab or window
          window.open(fileURL, '_blank');
        } else {
          console.error('Failed to fetch resume:', response.status);
        }
      } catch (error) {
        console.error('Error displaying resume:', error);
      }
    } else {
      console.error('No application ID available');
    }
  };
  const handleDisplayCoverLetter = async () => {
  };

  const handleOpen = () => {
    resetForm();
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    resetForm();
  };

  const resetForm = () => {
    setResumeFile(null);
    setCoverLetterFile(null);
    setResumeUploadDate(null);
    setCoverLetterUploadDate(null);
    setSubmissionStatus("pending");
  };

  return (
    <div>
      <Button
        onClick={handleOpen}
        variant="contained"
        sx={ApplyButtonStyles.apply}
      >
        Apply
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth={"lg"}
        sx={ApplyButtonStyles.popupSize}
      >
        {submissionStatus === "pending" ? (
          <>
            <div style={{ marginTop: "40px" }} />
            <Typography sx={ApplyButtonStyles.header}>
              Apply to {companyName}
            </Typography>
            <div style={{ marginBottom: "20px" }} />
            <Typography>
              <Typography sx={ApplyButtonStyles.heading2}>
                Please upload your resume and cover letter
              </Typography>
              <div style={{ marginBottom: "10px" }} />
              <div style={{ clear: "both" }} />
              <div style={ApplyButtonStyles.greyBox}>
                <div style={ApplyButtonStyles.greyBoxText}>Resume</div>
                <div style={{ marginBottom: "10px" }} />
                <div style={ApplyButtonStyles.buttonStyles}>
                  <div style={ApplyButtonStyles.buttonContainerStyles}>
                    <span style={ApplyButtonStyles.labelStyles}>PDF</span>
                    <span style={ApplyButtonStyles.fileNameStyles}>
                      {resumeFile ? resumeFile.name : "No file selected"}
                    </span>
                    <p style={ApplyButtonStyles.descriptionStyles}>
                      Uploaded on {resumeUploadDate || "No date available"}
                    </p>
                  </div>
                </div>
                <div style={ApplyButtonStyles.uploadContainer}>
                  <input
                    type="file"
                    id="resumeInput"
                    accept=".pdf"
                    style={{ display: "none" }}
                    onChange={(event) => handleFileChange(event, "resume")}
                  />
                  <button
                    style={ApplyButtonStyles.uploadbuttonStyles}
                    onClick={() => handleUploadButtonClick("resume")}
                  >
                    Upload Resume
                  </button>
                </div>
                <div style={ApplyButtonStyles.greyBox}>
                  <div style={ApplyButtonStyles.greyBoxText}>Cover Letter</div>
                  <div style={{ marginBottom: "10px" }} />
                  <div style={ApplyButtonStyles.buttonStyles}>
                    <div style={ApplyButtonStyles.buttonContainerStyles}>
                      <span style={ApplyButtonStyles.labelStyles}>PDF</span>
                      <span style={ApplyButtonStyles.fileNameStyles}>
                        {" "}
                        {coverLetterFile
                          ? coverLetterFile.name
                          : "No file selected"}
                      </span>
                      <p style={ApplyButtonStyles.descriptionStyles}>
                        Uploaded on{" "}
                        {coverLetterUploadDate || "No date available"}
                      </p>
                    </div>
                  </div>
                  <div style={ApplyButtonStyles.uploadContainer}>
                    <input
                      type="file"
                      id="coverLetterInput"
                      accept=".pdf"
                      style={{ display: "none" }}
                      onChange={(event) =>
                        handleFileChange(event, "coverLetter")
                      }
                    />
                    <button
                      style={ApplyButtonStyles.uploadbuttonStyles}
                      onClick={() => handleUploadButtonClick("coverLetter")}
                    >
                      Upload Cover Letter
                    </button>
                  </div>
                </div>
              </div>
              <div style={{ margin: "10px" }} />
              <DialogActions>
                <Button
                  variant="contained"
                  size="small"
                  sx={ApplyButtonStyles.cancelButton}
                  onClick={handleClose}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  sx={ApplyButtonStyles.saveButton}
                  button
                  onClick={handleSubmission}
                  disabled={!resumeFile || !coverLetterFile}
                >
                  Submit
                </Button>
              </DialogActions>
            </Typography>
          </>
        ) : (
          <>
            <div style={{ marginTop: "60px" }} />
            <Typography sx={ApplyButtonStyles.header}>
              Apply to {companyName}
            </Typography>
            <div style={{ marginBottom: "10px" }} />
            <Typography sx={ApplyButtonStyles.heading2}>
              Your application has succesfully been submitted!
            </Typography>
            <div style={{ marginBottom: '45px' }} />
            <div style={{ clear: 'both' }} />
            <div>
              <Button onClick={handleDisplayResume}>View Resume</Button>
              <Button onClick={handleDisplayCoverLetter}>View Cover Letter</Button>
            </div>           
          </>
        )}
      </Dialog>
    </div>
  );
}

const ApplyButtonStyles = {
  apply: {
    backgroundColor: "#5e17eb",
    boxShadow: "none",
    borderRadius: "15px",
    "&:hover": {
      backgroundColor: "#D3D3D3",
      boxShadow: "none",
    },
  },

  header: {
    fontFamily: "League Spartan",
    fontSize: "38px",
    color: "#5E17EB",
    marginLeft: "50px",
    fontWeight: "bold",
  },
  heading2: {
    fontFamily: "League Spartan",
    fontSize: "18px",
    color: "#393939",
    marginLeft: "50px",
    marginBottom: "45px",
    fontWeight: "bold",
  },
  greyBox: {
    background: "#F7F7F7",
    paddingTop: "20px",
    paddingBottom: "20px",
    height: "100%",
    width: "100%",
  },
  greyBoxText: {
    fontFamily: "League Spartan",
    paddingLeft: "100px",
    paddingTop: "5px",
    paddingBottom: "5px",
    fontWeight: "bold",
  },
  subTitle: {
    fontFamily: "League Spartan",
    fontSize: "18px",
    fontWeight: "bold",
    color: "#00000",
    marginLeft: "100px",
  },
  popupForm: {
    background: "#F7F7F7",
  },
  saveButton: {
    background: "#5E17EB",
  },
  cancelButton: {
    color: "#5E17EB",
    background: "#F7F7F7",
    border: "2px solid #5E17EB",
  },
  buttonStyles: {
    display: "flex",
    alignItems: "center",
    marginLeft: "100px",
    marginBottom: "10px",
    cursor: "pointer", // Add cursor style to indicate it's clickable
  },
  buttonContainerStyles: {
    borderRadius: "20px",
    padding: "10px",
    backgroundColor: "white",
    width: "700px",
    border: "1px solid black",
    background: "linear-gradient(to right, #5E17EB 8%, white 8%)",
    position: "relative",
    overflow: "hidden", // Hide overflowing content
  },
  labelStyles: {
    color: "white",
    fontWeight: "bold",
    marginLeft: "4px",
    position: "relative",
    top: "16px",
  },
  fileNameStyles: {
    marginLeft: "23px",
    fontWeight: "bold",
    position: "relative",
    top: "10px",
    overflow: "hidden", // Hide overflowing content
    whiteSpace: "nowrap", // Prevent wrapping
    textOverflow: "ellipsis", // Show ellipsis (...) for long filenames
  },
  descriptionStyles: {
    fontSize: "12px",
    marginTop: "5px",
    color: "rgba(0, 0, 0, 0.42)",
    marginLeft: "60px",
    position: "relative",
    top: "5px",
  },
  uploadbuttonStyles: {
    fontFamily: "League Spartan",
    fontWeight: "bold",
    fontSize: "16px",
    backgroundColor: "#F7F7F7",
    color: "#5E17EB",
    border: "2px solid #5E17EB",
    padding: "10px 20px",
    cursor: "pointer",
    borderRadius: "20px",
  },
  uploadContainer: {
    display: "flex",
    alignItems: "center",
    marginLeft: "100px",
  },
};
