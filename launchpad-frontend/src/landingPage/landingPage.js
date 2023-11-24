import React, { useState, useEffect } from "react";
import { Grid } from "@mui/material";
import { mock_data } from "./mockData";
import { useNavigate } from "react-router-dom";
import "./landingPage.css";
import { SubmittedIcon, ViewedIcon } from "../components/landingIcons";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableRow from "@mui/material/TableRow";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";

const theme = createTheme({
  palette: {
    primary: {
      main: "#5E17EB",
    },
  },
});

function StatusIcon(status) {
  if (status === "Applied") {
    return <SubmittedIcon />;
  } else if (status === "Reviewed") {
    return <ViewedIcon />;
  } else {
    return <></>;
  }
}

export function LandingPage({ userId, setPage }) {
  const [appsExpanded, setAppsExpanded] = useState(false);
  const [savedExpanded, setSavedExpanded] = useState(false);
  const [userData, setUserData] = useState({});
  const [applicationData, setApplicationData] = useState({});
  const [jobData, setJobData] = useState({});
  const [recommendedData, setRecommendedData] = useState({});
  const [companyData, setCompanyData] = useState({});
  const [loading1, setLoading1] = useState(true);
  const [loading2, setLoading2] = useState(true);
  const navigate = useNavigate();
  useEffect(() => {
    if (userId) {
      const userPromise = fetch(`/users/${userId}`).then((res) => res.json());
      const applicationsPromise = fetch(`/applications/${userId}`).then((res) =>
        res.json()
      );
      const recommendedJobsPromise = fetch(`/recommended-jobs/${userId}`).then(
        (res) => res.json()
      );

      Promise.all([userPromise, applicationsPromise, recommendedJobsPromise])
        .then(([userData, applicationData, recommendedData]) => {
          setUserData(userData);
          setApplicationData(applicationData);
          setRecommendedData(recommendedData);
          setLoading1(false);
        })
        .catch((error) => console.error("Error fetching user data:", error));
    }
  }, [userId]);

  useEffect(() => {
    const jobsPromise = fetch(
      `/jobs?type=null&duration=null&location=null`
    ).then((res) => res.json());
    const companiesPromise = fetch(`/companies`).then((res) => res.json());

    Promise.all([jobsPromise, companiesPromise])
      .then(([jobData, companyData]) => {
        setJobData(jobData);
        setCompanyData(companyData);
        setLoading2(false);
      })
      .catch((error) =>
        console.error("Error fetching job and company data:", error)
      );
  }, []);

  const jobsCompanyData =
    jobData.data && companyData.data && userData.data
      ? jobData.data.map((job) => {
          const companyRecord = companyData.data.find(
            (company) => company.companyId === job.companyId
          );
          const saved = userData.data[0].savedPostings.find(
            (posting) => posting.postingId === job.postingId
          );
          return {
            ...job,
            companyName: companyRecord.companyName,
            saved: saved ? true : false,
          };
        })
      : [];

  const recommendedCompanyData =
    recommendedData.data && companyData.data && userData.data
      ? recommendedData.data.map((job) => {
          const companyRecord = companyData.data.find(
            (company) => company.companyId === job.companyId
          );
          const saved = userData.data[0].savedPostings.find(
            (posting) => posting.postingId === job.postingId
          );
          return {
            ...job,
            companyName: companyRecord.companyName,
            saved: saved ? true : false,
          };
        })
      : [];

  const applicationsEnhanced = applicationData.data
    ? applicationData.data.map((app) => {
        const jobPosting = jobsCompanyData.find(
          (posting) => posting.postingId === app.postingId
        );
        return {
          ...app,
          ...jobPosting,
        };
      })
    : [];

  const savedPostings = jobsCompanyData.filter((job) => job.saved);

  const recommendedPostings = recommendedCompanyData.sort((a, b) => {
    return new Date(a.deadline) - new Date(b.deadline);
  });

  const clickedJob = (jobId) => {
    setPage(`/jobs/${jobId}`);
    navigate(`/jobs/${jobId}`);
  };

  if (loading1 || loading2) {
    return (
      <ThemeProvider theme={theme}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
          }}
        >
          <CircularProgress />
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <>
      <p style={PageStyles.top_banner}>
        Welcome Back, {userData?.data?.[0]?.firstName || "User"}!
      </p>
      <Grid container spacing={6}>
        <Grid item xs={8}>
          <p style={PageStyles.headings}>Applications</p>
          <TableContainer>
            <Table aria-label="simple table" style={PageStyles.table}>
              <TableBody>
                {applicationsEnhanced
                  .slice(0, appsExpanded ? applicationsEnhanced.length : 3)
                  .map((row, i) => (
                    <TableRow
                      key={i}
                      sx={PageStyles.tableRow}
                      onClick={() => {
                        clickedJob(row.postingId);
                      }}
                    >
                      <TableCell
                        component="th"
                        scope="row"
                        align="center"
                        style={{ paddingRight: 0 }}
                      >
                        <img
                          src={row.logo}
                          height={"40px"}
                          alt={row.companyName}
                        ></img>
                      </TableCell>
                      <TableCell>
                        <p style={PageStyles.job_title}>{row.postingTitle}</p>
                        <p style={PageStyles.company}>{row.companyName}</p>
                        <p style={PageStyles.details}>
                          {row.duration} {row.type}, {row.location}
                        </p>
                      </TableCell>
                      <TableCell align="center">
                        {StatusIcon(row.Status)}
                      </TableCell>
                    </TableRow>
                  ))}
                <TableRow
                  key={"end"}
                  sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                >
                  <TableCell
                    colSpan={3}
                    sx={PageStyles.see_more}
                    onClick={() => setAppsExpanded(!appsExpanded)}
                  >
                    {appsExpanded ? "See Less" : "See More"}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <p style={PageStyles.headings}>Saved Jobs</p>
          <TableContainer>
            <Table aria-label="simple table" style={PageStyles.table}>
              <TableBody>
                {savedPostings
                  .slice(0, savedExpanded ? savedPostings.length : 3)
                  .map((row, i) => (
                    <TableRow
                      key={i}
                      sx={PageStyles.tableRow}
                      onClick={() => {
                        clickedJob(row.postingId);
                      }}
                    >
                      <TableCell
                        component="th"
                        scope="row"
                        align="center"
                        style={{ paddingRight: 0 }}
                      >
                        <img
                          src={row.logo}
                          height={"40px"}
                          alt={row.companyName}
                        ></img>
                      </TableCell>
                      <TableCell>
                        <p style={PageStyles.job_title}>{row.postingTitle}</p>
                        <p style={PageStyles.company}>{row.companyName}</p>
                        <p style={PageStyles.details}>
                          {row.duration} {row.type}, {row.location}
                        </p>
                      </TableCell>
                    </TableRow>
                  ))}
                <TableRow
                  key={"end"}
                  sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                >
                  <TableCell
                    colSpan={3}
                    sx={PageStyles.see_more}
                    onClick={() => setSavedExpanded(!savedExpanded)}
                  >
                    {savedExpanded ? "See Less" : "See More"}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={4}>
          <p style={PageStyles.headings}>Recommended</p>
          <TableContainer>
            <Table aria-label="simple table" style={PageStyles.table}>
              <TableBody>
                {recommendedPostings.slice(0, 6).map((row, i) => (
                  <TableRow
                    key={i}
                    sx={PageStyles.tableRow}
                    onClick={() => {
                      clickedJob(row.postingId);
                    }}
                  >
                    <TableCell style={{ paddingLeft: 30, paddingRight: 20 }}>
                      <p style={PageStyles.job_title}>{row.postingTitle}</p>
                      <p style={PageStyles.company}>{row.companyName}</p>
                      <p style={PageStyles.details}>
                        {row.duration} {row.type}, {row.location}
                      </p>
                    </TableCell>
                    <TableCell
                      align="center"
                      style={{ paddingRight: 20 }}
                    ></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>
    </>
  );
}

const PageStyles = {
  top_banner: {
    fontFamily: "League Spartan",
    fontSize: "48px",
    fontWeight: "bold",
    marginBottom: 5,
  },
  headings: {
    color: "#5E17EB",
    fontSize: "32px",
    fontWeight: "bolder",
  },
  job_title: {
    fontSize: "20px",
    fontWeight: 500,
    marginTop: "4px",
    marginBottom: "0px",
  },
  company: {
    marginTop: "0px",
    marginBottom: "0px",
    fontSize: "18px",
    color: "#5E17EB",
  },
  details: {
    marginTop: "0px",
    marginBottom: "4px",
    fontSize: "14px",
    color: "Gray",
  },
  table: {
    borderRadius: "20px",
    overflow: "hidden",
    backgroundColor: "white",
  },
  tableRow: {
    height: "50px",
    "&:last-child td, &:last-child th": {
      border: 0,
    },
    borderColor: "#bcbcbc",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: "#D3D3D3",
    },
    "&:focus": {
      backgroundColor: "#D3D3D3",
    },
  },
  see_more: {
    textAlign: "center",
    color: "White",
    fontSize: "12px",
    padding: 0.5,
    cursor: "pointer",
    backgroundColor: "#5E17EB",
    "&:hover": {
      backgroundColor: "#814AEF",
    },
    "&:focus": {
      backgroundColor: "#814AEF",
    },
  },
};
