/*
    THIS IS THE SCRIPT WORKING IN THE WEBSITE TO LOAD THE CONTENT WHEN SCROLL EVENT IS TRIGGERED.
    UNDERSTAND THIS SCRIPT TO LOAD THE CONTENT TO BE SCRAPED FOR THE SPIDER
*/


/***SCROLL***/
$(window).on('scroll', function () {
    if ($(window).scrollTop() + $(window).height() >= $(document).height() * 3 / 4 && !inprocess) {
        var loadMovie = $('.movie-of-mood-list').hasClass('active');
        var loadMoodlists = $('.related-mood-lists').hasClass('active');
        var id_moodlist = MOODLIST;
        if (
            loadMovie
            && !loadedAllMovies
            && $('.watch-now-list .list-inline').find('a.active-sort').length == 0
        ) {
            var count = countMovie;
            $.ajax({
                method: 'post',
                url: '/movies/index/get-movies-for-pagination/',
                beforeSend: function () {
                    inprocess = true;
                },
                data: 'offset=' + count + '&moodList=' + id_moodlist + '&sorting=' + SORT,
                success: function (data) {
                    if (data == '' ) {
                        if ($('.switch-button .see-recommended-movies').length != 0) {
                            data = '<div class="text-center switch-button">' +
                                '<h2 class="color-light-dark font-bold">' +
                                'Didn\'t Find What You Were Looking For?' +
                                '</h2>' +
                                '<button class="btn btn-primary clear border text-uppercase m-t-lg xxl see-related-lists">' +
                                'see related lists' +
                                '</button>' +
                                '</div>';
                            $('.footer').removeClass('hidden');
                        }
                        loadedAllMovies = true;
                    }
                    $('#add ul.movies-list.nav').append(data);
                    countMovie += 20;
                    inprocess = false;
                }
            });
        }
        if (loadMoodlists && !loadedAllMoodLists) {
            var count = countMoodlists;
            $.ajax({
                method: 'post',
                url: '/movies/index/get-related-mood-lists',
                beforeSend: function () {
                    inprocess = true;
                },
                data: 'offset=' + count + '&id=' + id_moodlist,
                success: function (data) {
                    if (data == '' && $('.switch-button .see-recommended-movies').length != 0) {
                        data = '<div class="col-xs-12">' +
                            '<div class="text-center switch-button">' +
                            '<h2 class="color-light-dark font-bold">' +
                            'Didn\'t Find What You Were Looking For?' +
                            '</h2>' +
                            '<button class="btn btn-primary clear border text-uppercase m-t-lg xxl see-recommended-movies">' +
                            'See Similar Movies' +
                            '</button>' +
                            '</div>' +
                            '</div>';

                        $('.footer').removeClass('hidden');
                        loadedAllMoodLists = true;
                    }
                    $('.dib.full-page-w.film-card-row').append(data);
                    slice_str();
                    equalheight('.film-card-row .caption');
                    countMoodlists += 9;
                    inprocess = false;
                }
            });
        }

    }
});
