import { STUDENT_WEB } from '../../constants/studentWebDesign';

export const studentWorkspaceStyles = `
  .student-workspace :is(button, a):focus-visible { outline:2px solid ${STUDENT_WEB.brand}; outline-offset:3px; }
  .student-workspace, .student-workspace-main, .student-workspace-page {
    display:flex; flex:1; min-width:0; min-height:0;
  }
  .student-workspace { width:100%; max-width:100%; overflow:hidden; }
  .student-workspace-main { flex-direction:column; }
  .student-workspace-page { flex-direction:column; }
  .student-workspace-skip {
    position:absolute; z-index:5; left:12px; top:12px; transform:translateY(calc(-100% - 18px));
    background:white; padding:12px 16px; border-radius:12px; color:${STUDENT_WEB.primary};
  }
  .student-workspace-skip:focus { transform:none; }
  .student-workspace-sidebar, .student-workspace-topbar { display:none; }
  @media (min-width: 768px) {
    .student-workspace { color:${STUDENT_WEB.ink}; font: 15px NunitoRegular, system-ui, sans-serif; }
    .student-workspace-sidebar {
      display:flex; flex-direction:column; flex:none; width:${STUDENT_WEB.sidebarWidth}px; box-sizing:border-box;
      padding:18px 16px; overflow-y:auto; color:white; background:linear-gradient(165deg,${STUDENT_WEB.shellStart},#3F23AA,${STUDENT_WEB.shellEnd});
    }
    .student-workspace-sidebar.is-collapsed { width:80px; padding-inline:12px; }
    .student-workspace-brand { display:flex; align-items:center; gap:8px; padding:0 5px; min-height:45px; font:21px NunitoBlack, system-ui, sans-serif; white-space:nowrap; }
    .student-workspace-brand span span { color:#E5D9FF; }
    .student-workspace-brand small { display:block; margin-top:1px; color:#E5D9FF; font:11px NunitoSemiBold, system-ui, sans-serif; }
    .student-workspace-sidebar.is-collapsed .student-workspace-brand { justify-content:center; padding:0; }
    .student-workspace-sidebar.is-collapsed span { display:none; }
    .student-workspace-toggle, .student-workspace-sidebar a {
      display:flex; align-items:center; gap:12px; text-decoration:none; color:inherit; box-sizing:border-box;
      min-height:48px; border:1px solid transparent; border-radius:14px; font:15px NunitoBold, system-ui, sans-serif;
    }
    .student-workspace-toggle { min-height:44px; justify-content:center; background:#FFFFFF14; margin:15px 0 20px; cursor:pointer; }
    .student-workspace-sidebar nav a { padding:0 13px; margin-bottom:5px; white-space:nowrap; }
    .student-workspace-sidebar.is-collapsed nav a { justify-content:center; padding:0; }
    .student-workspace-sidebar a:hover, .student-workspace-toggle:hover { background:#FFFFFF20; }
    .student-workspace-sidebar a[aria-selected="true"], .student-workspace-sidebar a[aria-current="page"] { background:#704BE0; border-color:#A88CF3; }
    .student-workspace .student-workspace-sidebar :is(button, a):focus-visible { outline-color:${STUDENT_WEB.gold}; }
    .student-workspace-shortcuts { border-top:1px solid #FFFFFF36; padding-top:13px; margin-top:15px; }
    .student-workspace-companion {
      margin-top:auto; padding-top:26px; border-radius:24px;
      background:radial-gradient(ellipse 85% 27% at 4% 104%,#B193F9 0 65%,transparent 66%),
        radial-gradient(ellipse 95% 29% at 106% 106%,#AD8DED 0 63%,transparent 64%);
    }
    .student-workspace-companion .student-workspace-safety { padding:10px; background:#FFFFFF14; border-color:#FFFFFF36; white-space:normal; }
    .student-workspace-safety strong, .student-workspace-safety small { display:block; }
    .student-workspace-safety strong { color:${STUDENT_WEB.gold}; }
    .student-workspace-safety small { font-size:11px; margin-top:3px; color:#F2E9FF; }
    .student-workspace-sidebar.is-collapsed .student-workspace-companion { display:none; }
    .student-workspace-topbar {
      display:flex; z-index:3; align-items:center; justify-content:space-between; flex:none; gap:12px;
      min-height:74px; padding:0 28px; background:white; border-bottom:1px solid ${STUDENT_WEB.border};
    }
    .student-workspace-search {
      display:flex; align-items:center; position:relative; gap:9px; padding:0 13px; min-height:44px; min-width:100px; width:min(410px,48%);
      border:1px solid ${STUDENT_WEB.border}; border-radius:14px; background:${STUDENT_WEB.background}; color:${STUDENT_WEB.primary};
    }
    .student-workspace-search:focus-within { border-color:${STUDENT_WEB.brand}; box-shadow:0 0 0 2px ${STUDENT_WEB.soft}; }
    .student-workspace-search input { font:inherit; color:${STUDENT_WEB.ink}; background:none; border:0; height:42px; width:100%; min-width:0; }
    .student-workspace-search input:focus-visible { outline:0; }
    .student-workspace-search kbd { background:${STUDENT_WEB.soft}; color:${STUDENT_WEB.muted}; border-radius:8px; font:12px NunitoBold,system-ui,sans-serif; white-space:nowrap; padding:3px 6px; }
    .student-workspace-tools, .student-workspace-account, .student-workspace-stars { display:flex; align-items:center; gap:9px; }
    .student-workspace-tools { gap:12px; }
    .student-workspace-anchor { position:relative; }
    .student-workspace-account, .student-workspace-icon, .student-workspace-stars {
      min-height:44px; box-sizing:border-box; border:0; cursor:pointer; color:${STUDENT_WEB.primary}; background:${STUDENT_WEB.soft};
      border-radius:24px; font:14px NunitoBold, system-ui, sans-serif;
    }
    .student-workspace-icon { display:grid; place-items:center; width:44px; text-decoration:none; }
    .student-workspace-account { padding:4px 10px 4px 4px; color:${STUDENT_WEB.ink}; }
    .student-workspace-account span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:156px; }
    .student-workspace-account small { display:block; text-align:left; color:${STUDENT_WEB.muted}; font-size:11px; }
    .student-workspace-stars { white-space:nowrap; padding:4px 13px; color:#724C00; background:#FFF3C6; text-decoration:none; }
    .student-workspace-account:hover, .student-workspace-icon:hover { background:#E7DCFF; }
    .student-workspace-popover {
      position:absolute; right:0; top:calc(100% + 10px); width:230px; padding:9px; border-radius:16px;
      border:1px solid ${STUDENT_WEB.border}; background:white; box-shadow:0 10px 32px #26136321; color:${STUDENT_WEB.ink};
    }
    .student-workspace-search-results { right:auto; left:0; width:min(360px, 52vw); }
    .student-workspace-popover a { display:flex; align-items:center; min-height:44px; border-radius:10px; padding:0 10px; color:${STUDENT_WEB.primary}; text-decoration:none; font-family:NunitoBold, system-ui, sans-serif; }
    .student-workspace-popover a:hover { background:${STUDENT_WEB.soft}; }
    .student-workspace-popover p, .student-workspace-popover strong { margin:8px 10px; }
  }
  @media (min-width: 768px) and (max-width: 1050px) {
    .student-workspace-sidebar { width:208px; }
    .student-workspace-search kbd { display:none; }
    .student-workspace-account span { display:none; }
    .student-workspace-topbar { padding-inline:18px; }
  }
`;
