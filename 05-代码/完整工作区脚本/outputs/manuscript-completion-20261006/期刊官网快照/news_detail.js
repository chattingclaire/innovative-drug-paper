var _id = $("#newsId").val();
var NEWS_TITLE_LEFT_CENTER_CN = $("#newsTitleLeftCenterCN").val() ? $("#newsTitleLeftCenterCN").val() : "";
var NEWS_TITLE_LEFT_CENTER_EN = $("#newsTitleLeftCenterEN").val() ? $("#newsTitleLeftCenterEN").val() : "";
config.NEWS_TITLE_LEFT_CENTER_CN = NEWS_TITLE_LEFT_CENTER_CN;
config.NEWS_TITLE_LEFT_CENTER_EN = NEWS_TITLE_LEFT_CENTER_EN;

template.defaults.imports.config = config;

$.ajax({
    url: basePath + 'data/news/newsData',
    type: "post",
    data: {
        id: _id,
    },
    dataType: "json",
    success: function (data) {
        console.log("news content", data);
        console.log(template("newsContentArt", data.data));
        if ($("#newsContentArt").length > 0) {
            $(".box-article").html(template("newsContentArt", data.data));

            $.ajax({
                url: basePath + 'getVisitNewsRecord',
                type: "post",
                data: {
                    id: _id,
                },
                dataType: "json",
                success: function (data) {
                    if ($(".news-browse-num").length && data.result && data.result == "success") {
                        $(".news-browse-num").html(data.data);
                    }
                }
            })

            if (window.afterNewsDetailRender) {
                afterNewsDetailRender(data.data);
            }

            $(".weixin").click(function () {
                shareTools("weixin", $(this));
                if ($(this).parent().siblings(".weixinBox").css("display") == "none") {
                    $(this).parent().siblings(".weixinBox").show();
                }
            });
            $(".kongjian").click(function () {
                shareTools("qzone", $(this));
            });
            $(".xinlang").click(function () {
                shareTools("sina", $(this));
            });
        }
    }
})


