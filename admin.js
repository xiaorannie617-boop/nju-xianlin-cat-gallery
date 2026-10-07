function addCat(){



let cat={


"id":Date.now(),


"名字":
document.getElementById("name").value,


"活动区域":
document.getElementById("area").value,


"照片":
document.getElementById("photo").value,


"毛色":
document.getElementById("color").value,


"体型":
document.getElementById("size").value,


"性格":
document.getElementById("personality").value,


"常见行为":
document.getElementById("behavior").value,


"发现地点":
document.getElementById("place").value,


"备注":
document.getElementById("note").value,


"猫苑评价":[]


};




let text=

JSON.stringify(
cat,
null,
4
);



let blob=

new Blob(
[text],
{
type:"application/json"
}
);



let a=

document.createElement("a");


a.href=

URL.createObjectURL(blob);



a.download=

cat["名字"]+".json";



a.click();



alert(
"猫咪档案已生成"
);



}