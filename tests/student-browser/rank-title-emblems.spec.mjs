import { test, expect, sites, login } from '../browser/fixtures.mjs';

const names = ['Sắt III', 'Sắt II', 'Sắt I', 'Đồng III', 'Đồng II', 'Đồng I', 'Bạc III', 'Bạc II', 'Bạc I', 'Vàng III', 'Vàng II', 'Vàng I', 'Bạch Kim V', 'Bạch Kim IV', 'Bạch Kim III', 'Bạch Kim II', 'Bạch Kim I', 'Kim Cương V', 'Kim Cương IV', 'Kim Cương III', 'Kim Cương II', 'Kim Cương I', 'Cao Thủ', 'Đại Cao Thủ', 'Thách Đấu', 'Huyền Thoại'];
const milestones = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 37, 42, 47, 52, 57, 62, 67, 72, 77, 82, 87, 122, 162, 162];
for (const width of [360, 768, 1440]) {
  test('single rank guide renders at '+width+'px', async ({ page, app }, testInfo) => {
    app.realStudent = true;
    const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
    let profile = { displayName:'Bạn nhỏ',gradeLevel:5,joinedAt:null,classrooms:[],avatar:'star',leaderboardVisible:true,leaderboardNameHidden:true,publicAlias:'Hươu Sao',selectedTitle:null,stars:1,rank,highestRank:rank.name,position:1,stats:{lessons:3,quizzes:0,games:0,days:1,week:3,month:3,today:3,streak:1},titles:[],history:[] };
    await page.route('**/api/v1/student/profile', async route => {
      if(route.request().method()==='PUT') profile={...profile,...route.request().postDataJSON()};
      await route.fulfill({json:profile});
    });
    await page.route('**/api/v1/student/leaderboard*',route=>route.fulfill({json:{gradeLevel:5,ownPosition:1,entries:names.map((name,i)=>({position:i+1,alias:'Bạn '+(i+1),avatar:'star',stars:1,rank:{...rank,name},self:i===0}))}}));
    await page.route('**/api/v1/student/rank-milestones',route=>route.fulfill({json:names.map((name,i)=>({name,stars:milestones[i],top:i===25?200:null}))}));
    await page.setViewportSize({width,height:900});
    await login(page,'STUDENT');
    await expect(page.getByText('Tiện ích nhanh',{exact:true})).toBeVisible();
    await page.goto(sites.portal.origin+'/study/achievements');
    await expect(page.getByText('HẠNG THEO SAO',{exact:true})).toBeVisible();
    await expect(page.getByRole('button',{name:'Lộ trình rank',exact:true})).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({path:testInfo.outputPath('achievements.png'),fullPage:true});
    await page.getByRole('button',{name:'Xem các bậc xếp hạng',exact:true}).click();
    const guide=page.getByRole('dialog');
    await expect(guide.getByText('Các bậc xếp hạng',{exact:true})).toBeVisible();
    const rows = guide.getByTestId('rank-milestone');
    await expect(rows).toHaveCount(26);
    for (const [index, name] of names.entries()) {
      const row = rows.nth(index);
      await expect(row.getByText(name, {exact:true})).toBeVisible();
      if(index < 24) await expect(row.getByText((milestones[index+1]-milestones[index])+' sao để lên '+names[index+1],{exact:true})).toBeVisible();
    }
    await expect(guide.getByText('Cấp hiện tại',{exact:true})).toHaveCount(1);
    await expect(rows.first().getByText('Cấp hiện tại',{exact:true})).toBeVisible();
    await expect(rows.last().getByText('Từ 162 sao và thuộc Top 200 toàn hệ thống',{exact:true})).toBeVisible();
    await expect(rows.first().getByTestId('rank-star-filled')).toHaveCount(1);
    await expect(rows.first().getByTestId('rank-star-empty')).toHaveCount(2);
    await expect(rows.first().getByText('1/3 sao',{exact:true})).toBeVisible();
    await expect(rows.nth(1).getByTestId('rank-star-empty')).toHaveCount(3);
    await expect(rows.nth(11).getByTestId('rank-star-empty')).toHaveCount(4);
    await expect(rows.nth(12).getByTestId('rank-star-empty')).toHaveCount(5);
    await expect(rows.nth(22).getByText('0/35 sao',{exact:true})).toBeVisible();
    await expect(rows.nth(23).getByText('0/40 sao',{exact:true})).toBeVisible();
    await expect(rows.nth(24).getByTestId('rank-star-progress')).toHaveCount(0);
    await expect(rows.last().getByTestId('rank-star-progress')).toHaveCount(0);
    expect(await guide.evaluate(el => el.scrollWidth-el.clientWidth)).toBeLessThanOrEqual(1);
    await expect(guide.getByTestId('approved-emblem-image')).toHaveCount(23);
    await page.screenshot({path:testInfo.outputPath('rank-guide.png'),fullPage:true});
    await guide.getByRole('button',{name:'Đóng Các bậc xếp hạng',exact:true}).click();
    await expect(page.getByRole('button',{name:'Lộ trình rank',exact:true})).toBeVisible();
  });
}
