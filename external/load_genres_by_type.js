/*
    THIS IS THE SCRIPT WORKING IN THE WEBSITE TO LOAD THE GENRES BASED ON TYPE (TV SHOW OR MOVIE).
    UNDERSTAND THIS SCRIPT TO LOAD THE CONTENT TO BE SCRAPED FOR THE SPIDER
*/

$(document).on('click', '.owl-inline .owl-switch-wrapper .type-genre', function (e) {
    e.preventDefault();
    var type = $(this).data('type');
    $('.owl-inline .owl-switch-wrapper .type-genre.active')
      .removeClass('btn-primary').removeClass('active')
      .addClass('btn-default').addClass('inverse');
    $(this).removeClass('btn-default').removeClass('inverse')
      .addClass('active').addClass('btn-primary');
    $.post('/movies/index/get-genres-by-type', {type: type})
      .done(function (data) {
        $('#owl-demo').empty();
        $('#owl-demo').append(data);
        $("#owl-demo").data('owlCarousel').destroy();
        genreList();
        $('#sub-genres').addClass('hidden');
        $.post('/movies/index/get-trending-mood-lists', {type: type})
          .done(function (data) {
            countMoodlist = 9;
            $('.dib.full-page-w.film-card-row').empty();
            $('.dib.full-page-w.film-card-row').append(data);
            slice_str();
            equalheight('.film-card-row .caption');
          });
      });
    var scrollVal = $('body').hasClass('f-banner') ? 150 : 50;
    $(document).scrollTop($("#browse").offset().top - scrollVal);
  });
